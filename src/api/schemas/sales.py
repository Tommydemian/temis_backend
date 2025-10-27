from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MERCADO_PAGO = "mercado_pago"
    OTHER = "other"


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"


class OrderSource(Enum):
    TIENDANUBE = "tiendanube"
    WHATSAPP = "whatsapp"
    POS = "pos"
    MANUAL = "manual"


class DeliveryStatus(Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"


class ProductQty(BaseModel):
    product_id: int
    quantity: int


class SaleResponse(BaseModel):
    order_date: datetime
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal
    total_price: Decimal
    total_cost: Decimal
    profit: Decimal
