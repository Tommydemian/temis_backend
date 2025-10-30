# src/api/routes/integrations/tiendanube.py
import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from loguru import logger

from src.core.config import settings
from src.core.database import get_conn

router = APIRouter(prefix="/tiendanube", tags=["TiendaNube"])


@router.get("/auth-url")
async def get_auth_url():
    auth_url = (
        f"https://www.tiendanube.com/apps/authorize/token?"
        f"client_id={settings.TIENDANUBE_APP_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
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
            3,  # tenant_id
            access_token,
            store_id,
            user_id,
            scope,
            True,  # is_active
        )

        logger.info(f"Integration saved for tenant {3}")

        # Si llegaste acá, funcionó
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration_success=tiendanube"
        )

    except Exception as e:
        logger.error(f"DB error saving integration: {type(e).__name__}")

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration_error=db_error"
        )
