# src/routes/products.py
from fastapi import APIRouter, Depends

from src.database import get_conn
from src.services import check_production_availability, get_products_list

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
