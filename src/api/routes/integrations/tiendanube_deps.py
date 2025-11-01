import asyncpg
from fastapi import Depends
from loguru import logger

from src.core.database import get_conn
from src.core.exceptions import NotFoundError


async def get_store_credentials(
    conn: asyncpg.Connection = Depends(get_conn), tenant_id: int = 2
):
    logger.bind(tenant_id=tenant_id).info("Fetching credentials")

    row = await conn.fetchrow(
        "SELECT store_id, access_token FROM tiendanube_integration WHERE tenant_id = $1",
        tenant_id,
    )

    if row is None:
        raise NotFoundError(identifier="Store id", resource=str(tenant_id))

    return {"store_id": row["store_id"], "access_token": row["access_token"]}
