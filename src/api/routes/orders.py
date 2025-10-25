# src/routes/orders.py
from fastapi import APIRouter, Depends, status

from src.api.schemas import ManualOrderRequest, OrderStatus, PaymentMethod
from src.core.database import get_conn
from src.services.orders import create_new_order, fetch_order_detail, fetch_orders

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("")
async def get_orders(
    conn=Depends(get_conn),
    tenant_id: int = 3,
    status: OrderStatus | None = None,
    customer_id: int | None = None,
    payment_method: PaymentMethod | None = None,
):
    return await fetch_orders(
        conn=conn,
        status=status,
        customer_id=customer_id,
        payment_method=payment_method,
        tenant_id=tenant_id,
    )


@router.get("/{order_id}")
async def get_order(order_id: int, tenant_id: int = 3, conn=Depends(get_conn)):
    return await fetch_order_detail(order_id, tenant_id=tenant_id, conn=conn)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(order: ManualOrderRequest, conn=Depends(get_conn)):
    return await create_new_order(order, conn)
