# src/services.py
from datetime import datetime, timedelta, timezone
from typing import cast

import asyncpg
from fastapi import HTTPException
from jose import jwt
from loguru import logger
from passlib.context import CryptContext

from src.config import settings
from src.models import (
    ComponentAvailability,
    ComponentResponse,
    LoginRequest,
    Order,
    OrderRequest,
    OrderResponse,
    OrderResponseItem,
    OrderStatusEnum,
    TokenResponse,
    User,
    UserCreate,
)

# ============================================================================
# AUTH CONFIG
# ============================================================================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# ============================================================================
# AUTH SERVICES
# ============================================================================


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def register_user(
    user_data: UserCreate, conn: asyncpg.Connection
) -> TokenResponse:
    """Register new user and return JWT token"""
    password_hashed = hash_password(user_data.password)

    row = await conn.fetchrow(
        """
        INSERT INTO \"user\" (email, password_hash)
        VALUES ($1, $2)
        RETURNING id, email, password_hash, created_at, updated_at
        """,
        user_data.email,
        password_hashed,
    )

    user = User(**cast(dict, row))
    token = create_access_token(data={"sub": str(user.id), "tenant_id": user.tenant_id})

    return TokenResponse(access_token=token, token_type="bearer")


async def login_user(
    credentials: LoginRequest, conn: asyncpg.Connection
) -> TokenResponse:
    """Login user and return JWT token"""
    user_row = await conn.fetchrow(
        'SELECT * FROM "user" WHERE email = $1',
        credentials.email,
    )

    if not user_row:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user = User(**dict(user_row))

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(data={"sub": str(user.id), "tenant_id": user.tenant_id})
    return TokenResponse(access_token=token, token_type="bearer")


# ============================================================================
# PRODUCT SERVICES
# ============================================================================


async def get_products_list(conn: asyncpg.Connection, is_active: bool | None = None):
    """Get all products, optionally filtered by is_active"""
    if is_active is not None:
        return await conn.fetch("SELECT * FROM product WHERE is_active = $1", is_active)
    return await conn.fetch("SELECT * FROM product")


async def check_production_availability(
    product_name: str, quantity: int, conn: asyncpg.Connection
) -> dict:
    """Check if we can produce given quantity of product"""
    if quantity <= 0:
        raise HTTPException(400, {"error": "invalid_quantity"})

    product = await conn.fetchrow(
        "SELECT id FROM product WHERE name = $1", product_name
    )
    if not product:
        raise HTTPException(404, {"error": "product_not_found"})

    view = await conn.fetch(
        "SELECT * FROM check_production_availability($1::TEXT, $2::INT)",
        product_name,
        quantity,
    )

    row_list = [ComponentAvailability(**row) for row in view]

    return {
        "detailed_data": row_list,
        "can_produce": all(row.can_produce for row in row_list),
    }


# ============================================================================
# ORDER SERVICES
# ============================================================================


async def get_orders_list(
    conn: asyncpg.Connection, status: OrderStatusEnum | None
) -> list[Order]:
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
    return [Order(**row) for row in rows]


async def get_order_by_id(order_id: int, conn: asyncpg.Connection) -> OrderResponse:
    """Get order details with items"""
    rows = await conn.fetch(
        """
        SELECT 
            o.id,
            o.customer_name,
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
        raise HTTPException(404, {"error": "order_not_found"})

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

        logger.debug("Order record inserted", order_id=order_id)

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

        # 4. Calculate total
        total = sum(
            products_dict[item.product_id]["sale_price"] * item.quantity
            for item in order.items
        )

        # 5. Update order total
        await conn.execute(
            'UPDATE "order" SET total_price = $1 WHERE id = $2', total, order_id
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


# COMPONENTS


async def get_components_list(
    conn: asyncpg.Connection,
    is_active: bool | None = None,
    has_low_stock: bool | None = None,
) -> list[ComponentResponse]:
    query = "SELECT c.* FROM component AS c"
    conditions = []
    params = []
    param_count = 1

    if has_low_stock is not None and has_low_stock:
        query += " JOIN inventory_alert AS ia ON ia.component_id = c.id"
        conditions.append("ia.is_active = TRUE")

    print(query)

    if is_active is not None:
        conditions.append(f"c.is_active = ${param_count}")
        params.append(is_active)
        param_count += 1

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = await conn.fetch(query, *params)

    return [ComponentResponse(**row) for row in rows]
