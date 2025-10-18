from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class Account(BaseModel):
    id: int
    email: EmailStr
    password_hash: str
    created_at: datetime
    updated_at: datetime | None = None


class AccountCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CheckAvalProduct(BaseModel):
    ingredient_id: int
    ingredient_name: str
    available: float | int
    total_needed: float | int
    can_produce: bool
    missing_quantity: float | int


class ProductQty(BaseModel):
    product_id: int
    quantity: int


class OrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    delivery_date: datetime | None = None
    items: list[ProductQty]


class OrderCreate(OrderRequest):
    total_price: Decimal
    notes: str | None = None


class OrderResponseItems(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float | int
    subtotal: Decimal


class OrderQueryResponse(BaseModel):
    order_id: int
    customer_name: str
    total_price: Decimal
    items: list[OrderResponseItems]
