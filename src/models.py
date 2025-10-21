from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, EmailStr


class OrderStatusEnum(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(BaseModel):
    id: int
    email: EmailStr
    password_hash: str
    created_at: datetime
    updated_at: datetime | None = None
    tenant_id: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================================
# PRODUCTION MODELS
# ============================================================================


class ComponentAvailability(BaseModel):
    component_id: int
    component_name: str
    available: Decimal
    total_needed: Decimal
    can_produce: bool
    missing_quantity: Decimal


# ============================================================================
# ORDER MODELS
# ============================================================================


class ProductQty(BaseModel):
    product_id: int
    quantity: int


class Order(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    total_price: Decimal
    status: str
    notes: str | None = None
    delivery_date: datetime | None
    created_at: datetime


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


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    updated_at: datetime | None = None


# ============================================================================
# COMPONENT MODELS
# ============================================================================


class ComponentResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    unit_measure: str  # kg, litros, unidades, etc.
    current_stock: Decimal
    min_stock: Decimal
    last_cost_price: Decimal | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
