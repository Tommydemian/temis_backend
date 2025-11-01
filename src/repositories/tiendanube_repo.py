from asyncpg import (
    Connection,
    ForeignKeyViolationError,
    PostgresError,
    UniqueViolationError,
)
from loguru import logger

from src.api.schemas.tiendanube import TiendaNubeProductDB, TiendaNubeVariantDB


async def save_products_batch(products: list[TiendaNubeProductDB], conn: Connection):
    query = """
                INSERT INTO tiendanube_product (
                    tenant_id, tiendanube_id, name, description, handle, 
                    attributes, published, requires_shipping, free_shipping,
                    canonical_url, brand, category_ids, image_urls, tags,
                    tn_created_at, tn_updated_at, last_synced_at, sync_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 
                    $11, $12, $13, $14, $15, $16, NOW(), 'synced'
                )
                ON CONFLICT (tenant_id, tiendanube_id) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    handle = EXCLUDED.handle,
                    attributes = EXCLUDED.attributes,
                    published = EXCLUDED.published,
                    requires_shipping = EXCLUDED.requires_shipping,
                    free_shipping = EXCLUDED.free_shipping,
                    canonical_url = EXCLUDED.canonical_url,
                    brand = EXCLUDED.brand,
                    category_ids = EXCLUDED.category_ids,
                    image_urls = EXCLUDED.image_urls,
                    tags = EXCLUDED.tags,
                    tn_created_at = EXCLUDED.tn_created_at,
                    tn_updated_at = EXCLUDED.tn_updated_at,
                    last_synced_at = NOW(),
                    sync_status = 'synced',
                    updated_at = NOW()
            """

    values = [
        (
            p.tenant_id,
            p.tiendanube_id,
            p.name,
            p.description,
            p.handle,
            p.attributes,
            p.published,
            p.requires_shipping,
            p.free_shipping,
            p.canonical_url,
            p.brand,
            p.category_ids,
            p.images_url,
            p.tags,
            p.created_at,
            p.updated_at,
        )
        for p in products
    ]

    try:
        await conn.executemany(query, values)
    except UniqueViolationError as e:
        logger.error(
            "Unexpected UniqueViolation despite ON CONFLICT",
            batch_size=len(products),
            error=str(e),
        )
        raise  # Cambiar de pass a raise - querés investigar
    except ForeignKeyViolationError as e:
        logger.error(
            "FK violation saving products batch",
            batch_size=len(products),
            error=str(e),
            product_ids=[v.tiendanube_id for v in products[:5]],
        )
        raise
    except PostgresError as e:
        logger.error("Unexpected PostgresError", error=str(e))
        raise


async def save_variant_batch(variants: list[TiendaNubeVariantDB], conn: Connection):
    query = """
                INSERT INTO tiendanube_product_variant (
                    tenant_id, tiendanube_variant_id, product_id, values,
                    price, promotional_price, cost, sku, stock, stock_management,
                    weight, width, height, depth, tn_created_at, tn_updated_at,
                    last_synced_at, sync_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, NOW(), 'synced'
                )
                ON CONFLICT (tiendanube_variant_id)
                DO UPDATE SET
                    product_id = EXCLUDED.product_id,
                    values = EXCLUDED.values,
                    price = EXCLUDED.price,
                    promotional_price = EXCLUDED.promotional_price,
                    cost = EXCLUDED.cost,
                    sku = EXCLUDED.sku,
                    stock = EXCLUDED.stock,
                    stock_management = EXCLUDED.stock_management,
                    weight = EXCLUDED.weight,
                    width = EXCLUDED.width,
                    height = EXCLUDED.height,
                    depth = EXCLUDED.depth,
                    tn_created_at = EXCLUDED.tn_created_at,
                    tn_updated_at = EXCLUDED.tn_updated_at,
                    last_synced_at = NOW(),
                    sync_status = 'synced',
                    updated_at = NOW()
            """

    values = [
        (
            v.tenant_id,
            v.tiendanube_variant_id,
            v.product_id,
            v.values,
            v.price,
            v.promotional_price,
            v.cost,
            v.sku,
            v.stock,
            v.stock_management,
            v.weight,
            v.width,
            v.height,
            v.depth,
            v.tn_created_at,
            v.tn_updated_at,
        )
        for v in variants
    ]

    try:
        await conn.executemany(query, values)
    except UniqueViolationError as e:
        logger.error(
            "Unexpected UniqueViolation despite ON CONFLICT",
            batch_size=len(variants),
            error=str(e),
        )
        raise
    except ForeignKeyViolationError as e:
        logger.error(
            "FK violation saving variants batch",
            batch_size=len(variants),
            error=str(e),
            variant_ids=[v.tiendanube_variant_id for v in variants[:5]],
        )
        raise
    except PostgresError as e:
        logger.error("Unexpected PostgresError", error=str(e))
        raise
