# src/api/routes/integrations/tiendanube.py
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger

from src.api.routes.integrations.tiendanube_deps import get_store_credentials
from src.api.schemas import TiendaNubeProductDB
from src.core.config import settings
from src.core.database import get_conn
from src.services.tiendanube import sync_products_from_tiendanube

router = APIRouter(prefix="/tiendanube", tags=["TiendaNube"])


@router.get("/auth-url")
async def get_auth_url():
    auth_url = (
        f"https://www.tiendanube.com/apps/{settings.TIENDANUBE_APP_ID}/authorize?"
        f"redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=read_orders,write_orders,read_products,write_products"
    )

    return {"auth_url": auth_url}


@router.get("/callback")
async def tiendanube_callback(code: str, conn=Depends(get_conn)):
    # Paso 1: Intercambiar code por token
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.tiendanube.com/apps/authorize/token",
                json={
                    "client_id": settings.TIENDANUBE_APP_ID,
                    "client_secret": settings.TIENDANUBE_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                },
            )

            if response.status_code != 200:
                logger.error(f"TiendaNube OAuth failed: {response.status_code}")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/dashboard?integration_error=oauth_failed"
                )

            data = response.json()
            access_token = data["access_token"]
            store_id = str(data["user_id"])
            user_id = data["user_id"]
            scope = data.get("scope", "")

    except Exception as e:
        logger.error(f"OAuth exchange error: {type(e).__name__}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration_error=network_error"
        )

    try:
        await conn.execute(
            """
    INSERT INTO tiendanube_integration 
        (tenant_id, access_token, store_id, user_id, scope, is_active)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (tenant_id)
    DO UPDATE SET
        access_token = EXCLUDED.access_token,
        store_id = EXCLUDED.store_id,
        user_id = EXCLUDED.user_id,
        scope = EXCLUDED.scope,
        is_active = TRUE,
        updated_at = NOW()
    """,
            4,  # tenant_id
            access_token,
            store_id,
            user_id,
            scope,
            True,  # is_active
        )

        logger.info(f"Integration saved for tenant {4}")

        # Si llegaste acá, funcionó
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration_success=tiendanube"
        )

    except Exception as e:
        logger.error(f"DB error saving integration: {type(e).__name__}")

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration_error=db_error"
        )


@router.post("/products/sync")
async def sync_products(
    conn=Depends(get_conn), credentials=Depends(get_store_credentials)
):
    result = await sync_products_from_tiendanube(
        store_id=credentials["store_id"],
        access_token=credentials["access_token"],
        conn=conn,
    )

    return result


@router.get("/products")
async def get_products(
    conn=Depends(get_conn),
    page: int = 1,
    limit=50,
    tenant_id: int = 2,
    published: bool | None = None,
):
    offset = (page - 1) * limit

    query = "SELECT * FROM tiendanube_product WHERE tenant_id = $1"
    params = [tenant_id]

    count_query = "SELECT COUNT(*) FROM tiendanube_product WHERE tenant_id = $1"
    count_params = [tenant_id]

    if published is not None:
        query += " AND published = $2"
        params.append(published)
        query += " LIMIT $3 OFFSET $4"
        params.extend([limit, offset])
        count_query += " AND published = $2"
        count_params.append(published)
    else:
        query += " LIMIT $2 OFFSET $3"
        params.extend([limit, offset])

    rows = await conn.fetch(query, *params)
    total = await conn.fetchval(count_query, *count_params)
    products = [TiendaNubeProductDB(**row) for row in rows]

    return {"total": total, "page": page, "per_page": limit, "data": products}


@router.get("/categories")
async def tiendanube_get_categories(conn=Depends(get_conn)):
    credentials = await get_store_credentials(conn, tenant_id=2)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.tiendanube.com/v1/{credentials['store_id']}/products",
            headers={
                "Authentication": f"bearer {credentials['access_token']}",
                "User-Agent": "TALOS ERP (tomasgilamoedo@gmail.com)",
            },
        )

        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Total products: {response.headers.get('X-Total-Count')}")
        logger.info(f"Link header: {response.headers.get('Link')}")

        if response.status_code != 200:
            logger.error(f"TiendaNube API error: {response.status_code}")
            raise HTTPException(
                status_code=502, detail="Failed to fetch products from TiendaNube"
            )

        return response.json()

        # products = [TiendaNubeProduct(**el) for el in raw_products]

        # logger.info(len(products))

        # return raw_products
