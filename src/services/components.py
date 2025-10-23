import asyncpg

from src.api.schemas import ComponentResponse


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
