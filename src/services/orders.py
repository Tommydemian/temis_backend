import asyncpg
from loguru import logger

from src.api.schemas import (
    Customer,
    ManualOrderRequest,
    OrderBase,
    OrderStatus,
    PaymentMethod,
)
from src.api.schemas.orders import OrderResponseItem
from src.core.exceptions import NotFoundError


async def fetch_orders(
    conn: asyncpg.Connection,
    status: OrderStatus | None,
    payment_method: PaymentMethod | None,
    customer_id: int | None,
    tenant_id,
) -> list[OrderBase]:
    log = logger.bind(
        tenant_id=tenant_id,
        filters={
            "status": status.value if status else None,
            "payment_method": payment_method.value if payment_method else None,
            "customer_id": customer_id,
        },
    )

    log.info("Fetching orders with filters")
    # vars
    query = 'SELECT * FROM "order"'
    conditions = []
    params = []
    params_count = 1

    if tenant_id:
        params.append(tenant_id)
        conditions.append(f"tenant_id = ${params_count}")

    if status is not None:
        params.append(status.value)
        params_count += 1
        conditions.append(f"status = ${params_count}")

    if payment_method is not None:
        params.append(payment_method.value)
        params_count += 1
        conditions.append(f"payment_method = ${params_count}")

    if customer_id is not None:
        params.append(customer_id)
        params_count += 1
        conditions.append(f"customer_id = ${params_count}")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = await conn.fetch(query, *params)

    log.info("Orders retrieved", count=len(rows))

    return [OrderBase(**row) for row in rows]


async def fetch_order_detail(order_id: int, tenant_id: int, conn: asyncpg.Connection):
    """Get order details with items"""
    log = logger.bind(order_id=order_id, tenant_id=tenant_id)

    log.info("Fetching order details")

    order = await conn.fetchrow(
        'SELECT * FROM "order" WHERE id = $1 AND tenant_id = $2', order_id, tenant_id
    )

    if order is None:
        log.warning("Order not found")
        raise NotFoundError(resource="Order", identifier=order_id)

    log.info("Order retrieved successfully")

    items = await conn.fetch(
        "SELECT * FROM order_product WHERE order_id = $1 AND tenant_id = $2",
        order_id,
        tenant_id,
    )

    if not items:
        log.warning("Items not found")
        raise NotFoundError(resource="Order_items", identifier=order_id)

    order_items = [
        OrderResponseItem(
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            subtotal=row["quantity"] * row["unit_price"],
        )
        for row in items
    ]

    # Query 3: Ledger entries con lines agrupadas
    entries = await conn.fetch(
        """
        SELECT le.*, COALESCE(json_agg(ll.*), '[]'::json) as lines
        FROM ledger_entry le
        JOIN ledger_line ll ON le.id = ll.entry_id
        WHERE le.order_id = $1 AND le.tenant_id = $2
        GROUP BY le.id
    """,
        order_id,
        tenant_id,
    )

    if not entries:
        log.warning("Entries not found")
        raise NotFoundError(resource="Ledger entries", identifier=order_id)

    return {"order": order, "order_items": order_items, "accounting": entries}


async def create_new_order(order: ManualOrderRequest, conn: asyncpg.Connection) -> dict:
    """Create order with transaction"""
    logger.info(
        "Creating order",
        customer=order.customer_id,
        items_count=len(order.items),
        product_ids=[item.product_id for item in order.items],
    )
    # Handle delivery date
    # delivery_date = order.delivery_date
    # if delivery_date:
    #     if delivery_date.tzinfo is None:
    #         delivery_date = delivery_date.replace(tzinfo=timezone.utc)
    # else:
    #     delivery_date = datetime.now(timezone.utc) + timedelta(days=7)

    async with conn.transaction():
        logger.debug("Transaction started for order creation")

        customer: Customer | None = None

        if order.customer_id:
            customer = await conn.fetchrow(
                "SELECT * FROM customer WHERE id = $1 AND tenant_id = $2",
                order.customer_id,
                3,
            )

            if customer is None:
                logger.warning("Customer not found")
                raise NotFoundError(resource="Customer", identifier=order.customer_id)
            else:
                customer = Customer(**customer)
        # 1. Insert order
        order_row = await conn.fetchrow(
            """
            INSERT INTO "order"(customer_id, payment_method, notes, total_price, tenant_id) 
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at, order_date
            """,
            order.customer_id,
            order.payment_method.value,
            order.notes,
            1,
            3,
        )

        order_id = order_row["id"]
        order_date = order_row["order_date"]

        log = logger.bind(order_id=order_id)
        log.debug("Order record inserted")

        # 2. Get product prices
        products_id = [item.product_id for item in order.items]
        rows = await conn.fetch(
            """
            SELECT id, name, sale_price, historical_cost 
            FROM product
            WHERE id = ANY($1)
            """,
            products_id,
        )
        products_dict = {row["id"]: dict(row) for row in rows}

        log.debug("Products fetched", items_count=len(products_dict))

        # 3. Bulk insert order_product
        order_items_data = [
            (
                order_id,
                products_dict[item.product_id]["name"],
                item.product_id,
                item.quantity,
                products_dict[item.product_id]["sale_price"],
                21.00,
                3,
                # products_dict[item.product_id]["historical_cost"],
            )
            for item in order.items
        ]

        await conn.executemany(
            """
            INSERT INTO order_product (order_id, product_name, product_id, quantity, unit_price, iva_rate, tenant_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            order_items_data,
        )

        log.debug("Order items inserted", items_count=len(order_items_data))

        # 4. Calculate total
        total_price = sum(
            products_dict[item.product_id]["sale_price"] * item.quantity
            for item in order.items
        )

        log.debug("Total calculated", total_price=total_price)

        # 5. Update order total
        await conn.execute(
            'UPDATE "order" SET total_price = $1 WHERE id = $2', total_price, order_id
        )

        log.info(
            "Order created successfully",
            total_price=float(total_price),
            items_count=len(order.items),
        )

        # MVC COST
        mvc_cost = sum(
            products_dict[item.product_id]["historical_cost"] * item.quantity
            for item in order.items
        )

        entry_row = await conn.fetchrow(
            "INSERT INTO ledger_entry(tenant_id, entry_date, order_id) VALUES($1, $2, $3) RETURNING id",
            3,
            order_date,
            order_id,
        )

        entry_id = entry_row["id"]

        # 1. Obtener account_ids
        cash_or_bank_id = await conn.fetchval(
            "SELECT id FROM ledger_account WHERE code = $1 AND tenant_id = $2",
            "1.1" if order.payment_method == PaymentMethod.CASH.value else "1.2",
            3,
        )

        sales_account_id = await conn.fetchval(
            "SELECT id FROM ledger_account WHERE code = $1 AND tenant_id = $2",
            "4.1",  # Ventas
            3,
        )

        # Crear entry #2
        entry2_row = await conn.fetchrow(
            "INSERT INTO ledger_entry(tenant_id, entry_date, order_id) VALUES($1, $2, $3) RETURNING id",
            3,
            order_date,
            order_id,
        )
        entry2_id = entry2_row["id"]

        # Obtener account_ids
        cogs_id = await conn.fetchval(
            "SELECT id FROM ledger_account WHERE code = '5.1' AND tenant_id = $1", 3
        )
        inventory_id = await conn.fetchval(
            "SELECT id FROM ledger_account WHERE code = '1.4' AND tenant_id = $1", 3
        )

        # Insertar líneas
        await conn.executemany(
            "INSERT INTO ledger_line(tenant_id, entry_id, account_id, debit, credit) VALUES ($1, $2, $3, $4, $5)",
            [
                (3, entry2_id, cogs_id, mvc_cost, 0),  # CMV DEBE
                (3, entry2_id, inventory_id, 0, mvc_cost),  # Inventario HABER
            ],
        )

        # 2. Insertar 2 líneas
        await conn.executemany(
            "INSERT INTO ledger_line(tenant_id, entry_id, account_id, debit, credit) VALUES ($1, $2, $3, $4, $5)",
            [
                (3, entry_id, cash_or_bank_id, total_price, 0),  # DEBE
                (3, entry_id, sales_account_id, 0, total_price),  # HABER
            ],
        )

        return {
            "order_id": order_id,
            "status": "pending",
            "total_price": float(total_price),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": products_dict[item.product_id]["name"],
                    "quantity": item.quantity,
                    "unit_price": float(products_dict[item.product_id]["sale_price"]),
                    "subtotal": float(
                        products_dict[item.product_id]["sale_price"] * item.quantity
                    ),
                }
                for item in order.items
            ],
            "created_at": order_row["created_at"],
        }
