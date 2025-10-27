import asyncpg
from loguru import logger

from src.api.schemas import SaleResponse

# Fecha | Código | Cantidad | Precio Unit | Costo | Ingreso | Costo Total | Ganancia
# ```


async def fetch_sales_report(
    conn: asyncpg.Connection, tenant_id: int = 3
) -> list[SaleResponse] | list:
    logger.info("Fetching sales report")
    log = logger.bind(tenant_id=tenant_id)

    view = await conn.fetch(
        """
    SELECT
        ORDER_DATE,
        CUSTOMER_ID,
        STATUS,
        TOTAL_PRICE,
        PAYMENT_METHOD,
        P.SKU,
        OP.PRODUCT_ID,
        OP.PRODUCT_NAME,
        OP.QUANTITY,
        OP.UNIT_PRICE,
        OP.UNIT_COST,
        OP.QUANTITY * OP.UNIT_PRICE AS TOTAL,
        OP.UNIT_COST * OP.QUANTITY AS TOTAL_COST,
        (OP.QUANTITY * OP.UNIT_PRICE) - (OP.UNIT_COST * OP.QUANTITY) AS PROFIT
    FROM
        "order" AS O
        JOIN ORDER_PRODUCT AS OP ON OP.ORDER_ID = O.ID
        JOIN PRODUCT AS P ON OP.PRODUCT_ID = P.ID
    WHERE
        O.TENANT_ID = $1
    ORDER BY
        P.ID
    """,
        tenant_id,
    )

    if not view:
        log.warning("Sales not found")
        return []

    sales_data = [SaleResponse(**row) for row in view]

    log.info("Sales fetched successfully", items_count=len(sales_data))

    return sales_data
