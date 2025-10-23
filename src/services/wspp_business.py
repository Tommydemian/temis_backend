import asyncpg


async def get_wspp_customer(
    phone: str,
    conn: asyncpg.Connection,
    name: str | None = None,
):
    data = {"phone": phone, "name": name}
    customer = await conn.fetchrow(
        "SELECT * FROM customer where phone = $1 AND tenant_id = $2",
        phone,
        2,
    )

    if customer is None:
        customer = await conn.execute(
            "INSERT INTO customer(name, phone, tenant_id)VALUES($1, $2, $3)RETURNING *",
            data.get("name"),
            data.get("phone"),
            2,
        )

    return customer

async def create_order()
