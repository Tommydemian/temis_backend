from fastapi import APIRouter, Depends

from src.core.database import get_conn
from src.services.sales import fetch_sales_report

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/reports")
async def get_sales_report(
    tenant_id: int = 3,
    conn=Depends(get_conn),
):
    return await fetch_sales_report(conn=conn, tenant_id=tenant_id)
