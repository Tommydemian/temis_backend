# src/services/invoice_service.py
# from decimal import Decimal
from dataclasses import asdict
from datetime import date
from decimal import Decimal

import asyncpg
from fastapi import HTTPException

from src.models import Factura, FacturaB, FacturaC, IVAItem
from src.services.afip.afip_service import get_next_invoice_number

# 80 = CUIT
# 86 = CUIL
# 96 = DNI
# 99 = Consumidor Final
TAX_ID_B_CODES = [80, 86, 96]


async def create_invoice_from_order(order_id: int, conn: asyncpg.Connection) -> dict:
    """Creates invoice from order, requests CAE, saves to DB."""
    # get order
    row = await conn.fetchrow(
        """
    SELECT 
        o.*,
        c.tax_id_type,
        c.tax_id_number,
        c.tax_regime,
        c.name as customer_name,
        c.address as customer_address
    FROM "order" o
    LEFT JOIN customer c ON o.customer_id = c.id
    WHERE o.id = $1 AND o.tenant_id = $2
    """,
        order_id,
        2,
    )

    if row is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    customer_id = row.get("customer_id")

    invoice_type: int
    # Átomo 1: Sin customer → C
    if customer_id is None:
        invoice_type = 11

    # Átomo 2: >= $10M → B obligatorio (PRIMERO)
    elif row["total_price"] >= 10_000_000:
        if not row.get("tax_id_number"):
            raise HTTPException(400, ">=10M requires identification")
        invoice_type = 6

    # Átomo 3: Tiene tax_id → B
    elif row.get("tax_id_type") in [80, 86, 96]:
        invoice_type = 6

    # Átomo 4: Default → C
    else:
        invoice_type = 11

        # 1 = Productos
        # 2 = Servicios
        # 3 = Productos y Servicios
    concept = 1
    point_of_sale = 1

    invoice_number = get_next_invoice_number(
        point_of_sale=point_of_sale, invoice_type=invoice_type
    )

    # Calculate amounts
    total = Decimal(str(row["total_price"]))

    if invoice_type == 6:  # Factura B - discriminate IVA
        neto = total / Decimal("1.21")
        iva_amount = total - neto

        common_params = asdict(
            Factura(
                CantReg=1,
                PtoVta=point_of_sale,
                CbteTipo=invoice_type,
                Concepto=concept,
                DocTipo=int(row.get("tax_id_type")),
                DocNro=int(row.get("tax_id_number")) if invoice_type == 6 else 0,
                CbteDesde=invoice_number,
                CbteHasta=invoice_number,
                FchServDesde=None,
                FchServHasta=None,
                FchVtoPago=None,
                CbteFch=date.today(),
                ImpTotal=total,
                ImpNeto=neto,
            )
        )

        data = FacturaB(
            **common_params,
            ImpIVA=iva_amount,
            Iva=[IVAItem(Id=5, BaseImp=neto, Importe=iva_amount)],
        )
    elif invoice_type == 11:  # Factura C - no discrimination
        data = FacturaC(
            CantReg=1,
            PtoVta=point_of_sale,
            CbteTipo=invoice_type,
            Concepto=concept,
            DocTipo=99,  # Consumidor Final
            DocNro=0,
            CbteDesde=invoice_number,
            CbteHasta=invoice_number,
            FchServDesde=None,
            FchServHasta=None,
            FchVtoPago=None,
            CbteFch=date.today(),
            ImpTotal=total,
            ImpNeto=total,
        )

    # TODO: Call request_cae(data) and save to DB
    return {}
    pass
