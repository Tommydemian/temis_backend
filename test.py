import asyncpg
from loguru import logger

from src.core.config import settings


async def test_errors():
    conn = await asyncpg.connect(settings.DATABASE_URL)

    try:
        await conn.execute("""
            INSERT INTO tiendanube_product_variant (
                tenant_id, tiendanube_variant_id, product_id, values,
                price, sku, stock, tn_created_at, tn_updated_at,
                last_synced_at, sync_status
            ) VALUES (
                2, 99999999, 99999999, '{}',
                1000.0, 'SKU-TEST', 10, NOW(), NOW(),
                NOW(), 'synced'
            )
        """)
    except asyncpg.ForeignKeyViolationError as e:
        logger.error(f"ForeignKeyViolationError: {e}")

    await conn.close()


import asyncio

asyncio.run(test_errors())
