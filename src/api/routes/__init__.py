# src/routes/__init__.py
from fastapi import APIRouter

from src.api.routes import (
    auth,
    components,
    exports,
    orders,
    products,
    sales,
)
from src.api.routes.integrations import integrations_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(components.router)
api_router.include_router(sales.router)
api_router.include_router(exports.router)
api_router.include_router(integrations_router)
