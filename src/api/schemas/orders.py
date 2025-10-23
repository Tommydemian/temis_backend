from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    mercado_pago = "mercado_pago"
    other = "other"


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


class OrderBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Relations / tenancy
    customer_id: Optional[int] = None
    tenant_id: int

    # Order info
    order_date: Optional[datetime] = None  # DB default NOW() if None
    status: OrderStatus = OrderStatus.PENDING
    total_price: Decimal = Field(..., gt=0)
    notes: Optional[str] = None

    # Payment
    payment_method: Optional[PaymentMethod] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_date: Optional[datetime] = None

    # Source/channel
    source: Optional[OrderSource] = None

    # Delivery
    delivery_date: Optional[datetime] = None
    delivery_address: Optional[str] = None
    delivery_status: Optional[DeliveryStatus] = None
    delivery_notes: Optional[str] = None


class OrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    delivery_date: datetime | None = None
    items: list[ProductQty]


class OrderCreate(OrderRequest):
    total_price: Decimal
    notes: str | None = None


class OrderResponseItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal  # Cambié a Decimal
    subtotal: Decimal


class OrderResponse(BaseModel):
    order_id: int
    customer_name: str
    total_price: Decimal
    items: list[OrderResponseItem]
