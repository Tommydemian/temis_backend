from datetime import datetime, timedelta, timezone

import asyncpg
from loguru import logger

from src.api.schemas import (
    OrderBase,
    OrderRequest,
    OrderResponse,
    OrderResponseItem,
    OrderStatus,
)
from src.core.exceptions import NotFoundError


async def get_orders_list(
    conn: asyncpg.Connection, status: OrderStatus | None
) -> list[OrderBase]:
    # vars
    query = 'SELECT * FROM "order"'
    conditions = []
    params = []
    param_count = 1

    if status is not None:
        params.append(status.value)
        conditions.append(f"status = ${param_count}")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = await conn.fetch(query, *params)
    return [OrderBase(**row) for row in rows]


async def get_order_by_id(order_id: int, conn: asyncpg.Connection) -> OrderResponse:
    """Get order details with items"""
    log = logger.bind(order_id=order_id)

    logger.info("Fetching order details")

    rows = await conn.fetch(
        """
        SELECT 
            o.id,
            o.total_price,
            o.status,
            o.delivery_date,
            op.product_id,
            op.quantity, 
            op.unit_price,
            p.name, 
            p.category
        FROM "order" o
        JOIN order_product AS op ON o.id = op.order_id
        JOIN product AS p ON p.id = op.product_id
        WHERE o.id = $1
        """,
        order_id,
    )

    if not rows:
        logger.warning("Order not found")
        raise NotFoundError(resource="Order", identifier=order_id)

    items = [
        OrderResponseItem(
            product_id=row["product_id"],
            product_name=row["name"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            subtotal=row["quantity"] * row["unit_price"],
        )
        for row in rows
    ]

    log.info(
        "Order retrieved successfully",
        items_count=len(items),
        total_price=float(rows[0]["total_price"]),
    )

    return OrderResponse(
        order_id=order_id,
        customer_name=rows[0]["customer_name"],
        total_price=rows[0]["total_price"],
        items=items,
    )


async def create_new_order(order: OrderRequest, conn: asyncpg.Connection) -> dict:
    """Create order with transaction"""
    logger.info(
        "Creating order",
        customer=order.customer_name,
        items_count=len(order.items),
        product_ids=[item.product_id for item in order.items],
    )
    # Handle delivery date
    delivery_date = order.delivery_date
    if delivery_date:
        if delivery_date.tzinfo is None:
            delivery_date = delivery_date.replace(tzinfo=timezone.utc)
    else:
        delivery_date = datetime.now(timezone.utc) + timedelta(days=7)

    async with conn.transaction():
        logger.debug("Transaction started for order creation")
        # 1. Insert order
        order_row = await conn.fetchrow(
            """
            INSERT INTO "order"(customer_name, customer_phone, delivery_date) 
            VALUES ($1, $2, $3)
            RETURNING id, created_at
            """,
            order.customer_name,
            order.customer_phone,
            delivery_date,
        )

        order_id = order_row["id"]

        log = logger.bind(order_id=order_id)
        log.debug("Order record inserted")

        # 2. Get product prices
        products_id = [item.product_id for item in order.items]
        rows = await conn.fetch(
            """
            SELECT id, name, sale_price 
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
                item.product_id,
                item.quantity,
                products_dict[item.product_id]["sale_price"],
            )
            for item in order.items
        ]

        await conn.executemany(
            """
            INSERT INTO order_product (order_id, product_id, quantity, unit_price)
            VALUES ($1, $2, $3, $4)
            """,
            order_items_data,
        )

        log.debug("Order items inserted", items_count=len(order_items_data))

        # 4. Calculate total
        total = sum(
            products_dict[item.product_id]["sale_price"] * item.quantity
            for item in order.items
        )

        log.debug("Total calculated", total=total)

        # 5. Update order total
        await conn.execute(
            'UPDATE "order" SET total_price = $1 WHERE id = $2', total, order_id
        )

        log.info(
            "Order created successfully",
            total_price=float(total),
            items_count=len(order.items),
        )

        return {
            "order_id": order_id,
            "customer_name": order.customer_name,
            "status": "pending",
            "total_price": float(total),
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
