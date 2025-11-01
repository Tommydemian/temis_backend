import asyncpg
import httpx
from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError

from src.api.schemas import TiendaNubeProductDB, TiendaNubeVariantDB
from src.api.schemas.tiendanube import TiendaNubeProduct, Variant
from src.repositories import save_products_batch, save_variant_batch


async def _fetch_products_in_batches(
    store_id: str, access_token: str, batch_size: int = 50, tenant_id: int = 2
):
    products_batch = []
    variants_batch = []
    page = 1

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                f"https://api.tiendanube.com/v1/{store_id}/products",
                params={"page": page, "per_page": 30},
                headers={
                    "Authentication": f"bearer {access_token}",
                    "User-Agent": "TALOS ERP (tomasgilamoedo@gmail.com)",
                },
            )

            logger.info(f"Response headers: {response.headers}")
            logger.info(f"Total products: {response.headers.get('X-Total-Count')}")
            logger.info(f"Link header: {response.headers.get('Link')}")

            if response.status_code == 404:
                break

            if response.status_code != 200:
                logger.error(f"TiendaNube API error: {response.status_code}")
                raise HTTPException(
                    status_code=502, detail="Failed to fetch products from TiendaNube"
                )

            raw_products = response.json()

            # Parse and Transform:
            products = []
            variants = []
            for p in raw_products:
                try:
                    products.append(TiendaNubeProduct(**p))
                    variants.append([Variant(**var) for var in p.get("variants", [])])
                except ValidationError as e:
                    logger.warning(
                        "Validation error", id=p["id"], errors_list=e.errors()
                    )
                    continue

            db_products = [
                TiendaNubeProductDB.from_tiendanube_response(
                    tn_product=prod, tenant_id=tenant_id
                )
                for prod in products
            ]
            db_variants = [
                [
                    TiendaNubeVariantDB.from_tiendanube_variant(
                        variant=v, tenant_id=tenant_id
                    )
                    for v in variant_list
                ]
                for variant_list in variants
            ]

            for i, db_product in enumerate(db_products):
                products_batch.append(db_product)

                variants_batch.extend(db_variants[i])

                if len(products_batch) >= batch_size:
                    yield (products_batch, variants_batch)
                    products_batch = []
                    variants_batch = []

            page += 1

        # Yield last partial batch
        if products_batch:
            yield (products_batch, variants_batch)


async def sync_products_from_tiendanube(
    store_id: str, access_token: str, conn: asyncpg.Connection
):
    async for products, variants in _fetch_products_in_batches(
        store_id=store_id, access_token=access_token, batch_size=50
    ):
        await save_products_batch(products=products, conn=conn)
        await save_variant_batch(variants=variants, conn=conn)

    return {"status": "success", "synced": True}
