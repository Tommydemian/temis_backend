"""
API Schemas - Pydantic models for request/response validation
"""

from src.api.schemas.auth import (
    LoginRequest,
    TokenResponse,
    User,
    UserCreate,
    UserResponse,
)
from src.api.schemas.invoices import (
    CustomerTaxRegime,
    Factura,
    FacturaB,
    FacturaC,
    IVAItem,
    yyyymmdd,
)
from src.api.schemas.orders import (
    DeliveryStatus,
    OrderBase,
    OrderCreate,
    OrderRequest,
    OrderResponse,
    OrderResponseItem,
    OrderSource,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ProductQty,
)
from src.api.schemas.products import ComponentAvailability, ComponentResponse

__all__ = [
    # Auth
    "User",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    # Orders
    "OrderStatus",
    "PaymentMethod",
    "PaymentStatus",
    "OrderSource",
    "DeliveryStatus",
    "ProductQty",
    "OrderBase",
    "OrderRequest",
    "OrderCreate",
    "OrderResponseItem",
    "OrderResponse",
    # Products
    "ComponentAvailability",
    "ComponentResponse",
    # Invoices
    "CustomerTaxRegime",
    "IVAItem",
    "Factura",
    "FacturaC",
    "FacturaB",
    "yyyymmdd",
]
