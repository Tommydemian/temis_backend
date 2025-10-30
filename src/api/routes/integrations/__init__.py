# src/api/routes/integrations/__init__.py
from fastapi import APIRouter

from src.api.routes.integrations import tiendanube

integrations_router = APIRouter(prefix="/integrations", tags=["Integrations"])

integrations_router.include_router(tiendanube.router)
