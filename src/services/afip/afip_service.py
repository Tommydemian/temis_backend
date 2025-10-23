import os
from datetime import datetime

from afip import Afip

from config import settings
from src.models import FacturaB, FacturaC

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


# Solicitar CAE
# res = afip.ElectronicBilling.createVoucher(data)
# print(f"✓ CAE: {res['CAE']}")

# # Generar QR
# qr_json = {
#     "ver": 1,
#     "fecha": datetime.now().strftime("%Y-%m-%d"),
#     "cuit": config["CUIT"],
#     "ptoVta": data["PtoVta"],
#     "tipoCmp": data["CbteTipo"],
#     "nroCmp": data["CbteDesde"],
#     "importe": data["ImpTotal"],
#     "moneda": "PES",
#     "ctz": 1,
#     "tipoDocRec": data["DocTipo"],
#     "nroDocRec": data["DocNro"],
#     "tipoCodAut": "E",
#     "codAut": res["CAE"],
# }

# qr_string = json.dumps(qr_json)
# qr_b64_data = base64.b64encode(qr_string.encode()).decode()
# qr_url = f"https://www.afip.gob.ar/fe/qr/?p={qr_b64_data}"

# qr = qrcode.make(qr_url)
# buffer = BytesIO()
# qr.save(buffer, "PNG")
# qr_base64 = base64.b64encode(buffer.getvalue()).decode()

# # Cargar template
# with open("factura_template.html") as f:
#     template = Template(f.read())

# # Renderizar con datos
# html = template.render(
#     empresa_nombre="Tu Empresa",
#     empresa_cuit=config["CUIT"],
#     punto_venta=f"{data['PtoVta']:04d}",
#     numero_factura=f"{data['CbteDesde']:08d}",
#     fecha=datetime.now().strftime("%d/%m/%Y"),
#     cliente_cuit="-",
#     cliente_nombre="Consumidor Final",
#     cliente_condicion_iva="Consumidor Final",
#     items=[
#         {
#             "descripcion": "Producto de prueba",
#             "cantidad": "1",
#             "precio": "123.97",
#             "subtotal": "123.97",
#         }
#     ],
#     subtotal="123.97",
#     iva="26.03",
#     total="150.00",
#     cae=res["CAE"],
#     cae_vto=res["CAEFchVto"],
#     qr_base64=qr_base64,
# )

# # Generar PDF
# filename = f"factura_{data['PtoVta']:04d}_{data['CbteDesde']:08d}.pdf"
# HTML(string=html).write_pdf(filename)

# print(f"✓ PDF generado: {filename}")
