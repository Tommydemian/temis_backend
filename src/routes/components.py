# src/routes/orders.py
from fastapi import APIRouter, Depends

from src.database import get_conn
from src.models import ComponentResponse
from src.services import get_components_list

router = APIRouter(prefix="/components", tags=["Components"])


@router.get("", response_model=list[ComponentResponse])
async def get_components(
    is_active: bool | None = None,
    has_low_stock: bool | None = None,
    conn=Depends(get_conn),
):
    return await get_components_list(
        conn, is_active=is_active, has_low_stock=has_low_stock
    )


@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component_by_id(component_id: int, conn=Depends(get_conn)):
    row = await conn.fetchrow("SELECT * FROM component WHERE id = $1", component_id)
    res = ComponentResponse(**(row))
    return res
