import os
from datetime import datetime

from afip import Afip

from src.api.schemas import FacturaB, FacturaC
from src.core.config import settings

cert_path = os.path.expanduser("~/afip-certs/certificado.crt")
cert: str
key_path = os.path.expanduser("~/afip-certs/private.key")
key: str

with open(cert_path) as f:
    cert = f.read()

with open(key_path) as f:
    key = f.read()


config = {
    "CUIT": settings.CUIT,
    "production": False,  # Testing
    "cert": cert,
    "key": key,
}

DATE = datetime.now().strftime("%Y%m%d")
POINT_OF_SALE = 1
INVOICE_TYPE = 6  # B


def get_afip_client():
    try:
        return Afip(config)
    except Exception as e:
        print(e)
        raise


def get_next_invoice_number(point_of_sale: int, invoice_type: int) -> int:
    try:
        afip = get_afip_client()
        last = afip.ElectronicBilling.getLastVoucher(point_of_sale, invoice_type)
        return last + 1
    except Exception as e:
        print(e)
        raise


def request_cae(factura: FacturaB | FacturaC) -> dict:
    """Solicita CAE a AFIP. Retorna dict con CAE y vencimiento."""
    afip = get_afip_client()
    payload = factura.to_afip_payload()
    res = afip.ElectronicBilling.createVoucher(payload)
    return {"cae": res["CAE"], "cae_expiration": res["CAEFchVto"]}
