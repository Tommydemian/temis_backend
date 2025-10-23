import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from src.core.config import settings
from src.core.database import get_conn

router = APIRouter(prefix="/integrations/tiendanube", tags=["Integrations"])


@router.get("auth-url")
async def get_auth_url():
    auth_url = (
        "https://tiendanube/apps/authorize/token?"
        f"client_id={settings.TIENDANUBE_APP_ID}"
        f"&redirect_uri={settings.TIENDANUBE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=read_orders,write_orders,read_products,write_products"
    )

    return {"auth_url": auth_url}


@router.get("/callback")
async def tiendanube_callback(code: str, Depends=(get_conn)):
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
            raise HTTPException(status_code=400, detail="Failed to get access token")

        data = response.json()

        access_token = data["access_token"]
        user_id = data["user_id"]

        # 3. Guardar en DB (TODO: necesitamos saber QUÉ user de TU sistema está conectando)
        # Por ahora, placeholder:
        # await conn.execute(...)

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?integration=success"
        )
