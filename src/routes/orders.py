# src/routes/orders.py
from fastapi import APIRouter, Depends, status

from src.database import get_conn
from src.models import OrderRequest, OrderStatusEnum
from src.services.afip.services import (
    create_new_order,
    get_order_by_id,
    get_orders_list,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("")
async def get_orders(conn=Depends(get_conn), status: OrderStatusEnum | None = None):
    return await get_orders_list(conn=conn, status=status)


@router.get("/{order_id}")
async def get_order(order_id: int, conn=Depends(get_conn)):
    return await get_order_by_id(order_id, conn)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderRequest, conn=Depends(get_conn)):
    return await create_new_order(order, conn)
