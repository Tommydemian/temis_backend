import io

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.database import get_conn

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/inventory")
async def export_inventory(tenant_id: int = 3, conn=Depends(get_conn)):
    sql = """
        SELECT
            sku                                      AS "Código",
            name                                     AS "Título",
            supplier                                 AS "Proveedor",
            current_stock                            AS "Stock Actual",
            historical_cost                          AS "Costo Histórico (ARS)",
            replacement_cost                         AS "Costo Reposición (ARS)",
            sale_price                               AS "Precio Venta (ARS)"
        FROM product
        WHERE tenant_id = $1;
    """
    rows = await conn.fetch(sql, tenant_id)

    df = pd.DataFrame([dict(r) for r in rows])

    # Si está vacío, devolvé CSV vacío con headers
    if df.empty:
        csv_string = pd.DataFrame(
            columns=[
                "Código",
                "Título",
                "Proveedor",
                "Stock Actual",
                "Costo Histórico (ARS)",
                "Costo Reposición (ARS)",
                "Precio Venta (ARS)",
                "Ganancia (Venta)",
                "% Ganancia",
                "% Ganancia Repo",
            ]
        ).to_csv(index=False)
        return StreamingResponse(
            io.BytesIO(csv_string.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="inventario.csv"'},
        )

    # Asegurar numéricos (por si vienen Decimal/str)
    for col in [
        "Costo Histórico (ARS)",
        "Costo Reposición (ARS)",
        "Precio Venta (ARS)",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calcular ganancias y márgenes
    df["Ganancia (Venta)"] = df["Precio Venta (ARS)"] - df["Costo Histórico (ARS)"]
    df["% Ganancia"] = (
        ((df["Ganancia (Venta)"] / df["Precio Venta (ARS)"]) * 100)
        .round()
        .astype("Int64")
    )
    df["% Ganancia Repo"] = (
        (
            (
                (df["Precio Venta (ARS)"] - df["Costo Reposición (ARS)"])
                / df["Precio Venta (ARS)"]
            )
            * 100
        )
        .round()
        .astype("Int64")
    )

    csv_string = df.to_csv(index=False)
    logger.info("Export inventory CSV generated")

    return StreamingResponse(
        io.BytesIO(csv_string.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="inventario.csv"'},
    )
