from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class CustomerTaxRegime(Enum):
    MONOTRIBUTISTA = "Monotributista"
    RESPONSABLE_INSCRIPTO = "Responsable Inscripto"
    CONSUMIDOR_FINAL = "Consumidor Final"
    EXENTO = "Exento"


#  AFIP
# --- util ---
def yyyymmdd(d: Optional[date]) -> Optional[int]:
    return int(d.strftime("%Y%m%d")) if d else None


# --- ítems de IVA (solo Factura B) ---
@dataclass(slots=True)
class IVAItem:
    Id: int  # p.ej. 5 = 21%
    BaseImp: Decimal
    Importe: Decimal


# --- base ---
@dataclass(slots=True)
class Factura:
    CantReg: int
    PtoVta: int
    CbteTipo: int  # 6=B, 11=C (AFIP)
    Concepto: int  # 1 Prod, 2 Serv, 3 Ambos
    DocTipo: int  # 80 CUIT, 86 CUIL, 96 DNI, 99 CF
    DocNro: int
    CbteDesde: int
    CbteHasta: int
    CbteFch: date
    ImpTotal: Decimal
    ImpNeto: Decimal
    ImpOpEx: Decimal = Decimal("0")
    ImpTotConc: Decimal = Decimal("0")
    ImpTrib: Decimal = Decimal("0")
    MonId: str = "PES"
    MonCotiz: Decimal = Decimal("1")
    CondicionIVAReceptorId: Optional[int] = None
    FchServDesde: Optional[date] = None
    FchServHasta: Optional[date] = None
    FchVtoPago: Optional[date] = None

    def __post_init__(self):
        # Si es servicio (2/3), fechas obligatorias
        if self.Concepto in (2, 3):
            if not (self.FchServDesde and self.FchServHasta and self.FchVtoPago):
                raise ValueError(
                    "Para Concepto 2/3 se requieren FchServDesde/FchServHasta/FchVtoPago"
                )

    def to_payload_base(self) -> dict:
        return {
            "CantReg": self.CantReg,
            "PtoVta": self.PtoVta,
            "CbteTipo": self.CbteTipo,
            "Concepto": self.Concepto,
            "DocTipo": self.DocTipo,
            "DocNro": self.DocNro,
            "CbteDesde": self.CbteDesde,
            "CbteHasta": self.CbteHasta,
            "CbteFch": yyyymmdd(self.CbteFch),
            "FchServDesde": yyyymmdd(self.FchServDesde),
            "FchServHasta": yyyymmdd(self.FchServHasta),
            "FchVtoPago": yyyymmdd(self.FchVtoPago),
            "ImpTotal": float(self.ImpTotal),
            "ImpTotConc": float(self.ImpTotConc),
            "ImpNeto": float(self.ImpNeto),
            "ImpOpEx": float(self.ImpOpEx),
            "ImpTrib": float(self.ImpTrib),
            "MonId": self.MonId,
            "MonCotiz": float(self.MonCotiz),
            "CondicionIVAReceptorId": self.CondicionIVAReceptorId,
        }

    def to_afip_payload(self) -> dict:
        # Subclases pueden extender/ajustar
        return self.to_payload_base()


# --- Factura C: no discrimina IVA ---
@dataclass(slots=True)
class FacturaC(Factura):
    def __post_init__(self):
        super().__post_init__()
        # En C el IVA no se discrimina
        if self.CbteTipo != 11:
            raise ValueError("FacturaC requiere CbteTipo=11")
        if self.ImpOpEx != 0 or self.ImpTotConc < 0:
            # podés ajustar esta regla según tu negocio
            pass
        # Suele cumplirse: ImpTotal == ImpNeto + ImpTotConc + ImpOpEx + ImpTrib
        if self.ImpTotal != (
            self.ImpNeto + self.ImpTotConc + self.ImpOpEx + self.ImpTrib
        ):
            # No raise: a veces redondeos; podés normalizar acá si querés
            pass


# --- Factura B: discrimina IVA (Iva items) ---
@dataclass(slots=True)
class FacturaB(Factura):
    Iva: List[IVAItem] = field(default_factory=list)
    ImpIVA: Decimal = Decimal("0")

    def __post_init__(self):
        super().__post_init__()
        if self.CbteTipo != 6:
            raise ValueError("FacturaB requiere CbteTipo=6")
        # Si no te pasan ImpIVA, lo calculamos desde items
        if self.ImpIVA == 0 and self.Iva:
            self.ImpIVA = sum((i.Importe for i in self.Iva), Decimal("0"))
        # Chequeo de consistencia total
        esperado = (
            self.ImpNeto + self.ImpTotConc + self.ImpOpEx + self.ImpIVA + self.ImpTrib
        )
        if self.ImpTotal != esperado:
            # Podés normalizar o lanzar; aquí solo avisarías/loggear
            pass

    def to_afip_payload(self) -> dict:
        base = self.to_payload_base()
        base["ImpIVA"] = float(self.ImpIVA)
        base["Iva"] = [
            {"Id": it.Id, "BaseImp": float(it.BaseImp), "Importe": float(it.Importe)}
            for it in self.Iva
        ]
        return base
