# src/routes/__init__.py
from fastapi import APIRouter

from src.api.routes import auth, components, integrations, orders, products

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(components.router)
api_router.include_router(integrations.router)
