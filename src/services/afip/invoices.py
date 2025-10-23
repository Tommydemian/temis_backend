# src/services/invoice_service.py
# from decimal import Decimal
from dataclasses import asdict
from datetime import date
from decimal import Decimal

import asyncpg
from fastapi import HTTPException

from src.models import Factura, FacturaB, FacturaC, IVAItem
from src.services.afip.client import get_next_invoice_number, request_cae

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

    # Query para obtener concepts de productos
    product_concepts = await conn.fetch(
        """
        SELECT DISTINCT p.concept
        FROM order_product op
        JOIN product p ON op.product_id = p.id
        WHERE op.order_id = $1
    """,
        order_id,
    )

    concepts = {row["concept"] for row in product_concepts}

    if len(concepts) == 1:
        concept = concepts.pop()  # Todos iguales
    else:
        concept = 3  # Mix

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

    response = request_cae(data)  # Tu función AFIP
    cae = response["CAE"]
    cae_expiration = response["FchVto"]

    # 2. Guardar invoice en DB con SNAPSHOT
    await conn.execute(
        """
        INSERT INTO invoice (
            order_id,
            invoice_type,
            point_of_sale,
            invoice_number,
            invoice_date,
            cae,
            cae_expiration,
            total_amount,
            net_amount,
            iva_amount,
            -- SNAPSHOT del customer (frozen data)
            customer_name,
            customer_tax_id_type,
            customer_tax_id_number,
            customer_tax_regime,
            customer_address,
            customer_phone,
            customer_email,
            status,
            tenant_id
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19
        )
    """,
        order_id,
        "B" if invoice_type == 6 else "C",
        point_of_sale,
        invoice_number,
        date.today(),
        cae,
        cae_expiration,
        total,
        neto,
        iva_amount,
        # Snapshot fields (from row)
        row.get("customer_name"),  # ← frozen
        row.get("tax_id_type"),  # ← frozen
        row.get("tax_id_number"),  # ← frozen
        row.get("tax_regime"),  # ← frozen
        row.get("customer_address"),  # ← frozen
        row.get("phone"),  # ← frozen (falta en tu query)
        row.get("email"),  # ← frozen (falta en tu query)
        "approved",
        tenant_id,
    )

    return {
        "success": True,
        "invoice_id": invoice_id,
        "invoice_type": "B" if invoice_type == 6 else "C",
        "invoice_number": f"{point_of_sale:04d}-{invoice_number:08d}",
        "cae": cae,
        "total_amount": float(total),
        "status": "approved",
    }
