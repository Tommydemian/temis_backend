# src/routes/products.py
from fastapi import APIRouter, Depends

from src.core.database import get_conn
from src.services.products import (
    check_production_availability,
    get_products_list,
    search_products,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("")
async def get_products(
    is_active: bool | None = None,
    conn=Depends(get_conn),
):
    return await get_products_list(conn, is_active)


@router.get("/check-availability")
async def check_availability(product_name: str, quantity: int, conn=Depends(get_conn)):
    return await check_production_availability(product_name, quantity, conn)


@router.get("/search")
async def get_search_products(query: str, tenant_id: int = 3, conn=Depends(get_conn)):
    return await search_products(query=query, tenant_id=tenant_id, conn=conn)
