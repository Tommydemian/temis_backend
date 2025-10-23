import asyncpg

from src.api.schemas import ComponentAvailability
from src.core.exceptions import InvalidQuantityError, NotFoundError


async def get_products_list(conn: asyncpg.Connection, is_active: bool | None = None):
    """Get all products, optionally filtered by is_active"""
    if is_active is not None:
        await conn.fetch("SELECT * FROM product WHERE is_active = $1", is_active)
    return await conn.fetch("SELECT * FROM product")


async def check_production_availability(
    product_name: str, quantity: int, conn: asyncpg.Connection
) -> dict:
    """Check if we can produce given quantity of product"""
    if quantity <= 0:
        raise InvalidQuantityError(quantity=quantity)

    product = await conn.fetchrow(
        "SELECT id FROM product WHERE name = $1", product_name
    )
    if not product:
        raise NotFoundError(identifier="Product", resource=product_name)

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
