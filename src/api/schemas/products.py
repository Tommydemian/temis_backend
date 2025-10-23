from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ComponentAvailability(BaseModel):
    component_id: int
    component_name: str
    available: Decimal
    total_needed: Decimal
    can_produce: bool
    missing_quantity: Decimal


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
