from datetime import datetime
from decimal import Decimal
from typing import Optional

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


class ProductBase(BaseModel):
    name: str
    description: Optional[str]
    sku: str
    sale_price: Decimal
    category: Optional[str]
    current_stock: Decimal
    min_stock: Optional[Decimal]
    tenant_id: int
    iva_rate: Decimal
    replacement_cost: Optional[Decimal] = None
    supplier: Optional[str]


class Product(ProductBase):
    id: int
    created_at: datetime
    is_active: bool
    requires_production: bool
    concept: int


# -- Table: public.product

# -- DROP TABLE IF EXISTS public.product;

# CREATE TABLE IF NOT EXISTS public.product
# (
#     id integer NOT NULL DEFAULT nextval('product_id_seq'::regclass),
#     name character varying(100) COLLATE pg_catalog."default" NOT NULL,
#     description text COLLATE pg_catalog."default",
#     sku character varying(50) COLLATE pg_catalog."default",
#     replacement_cost numeric(8,2),
#     sale_price numeric(8,2) NOT NULL,
#     category character varying(50) COLLATE pg_catalog."default",
#     current_stock numeric(10,2),
#     min_stock numeric(10,2),
#     is_active boolean DEFAULT true,
#     requires_production boolean DEFAULT false,
#     iva_rate numeric(5,2) DEFAULT 21.00,
#     created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
#     tenant_id bigint NOT NULL,
#     concept integer NOT NULL DEFAULT 1,
#     historical_cost numeric(8,2),
#     supplier character varying(50) COLLATE pg_catalog."default",
#     CONSTRAINT product_pkey PRIMARY KEY (id),
#     CONSTRAINT product_tenant_id_sku_key UNIQUE (tenant_id, sku),
#     CONSTRAINT product_tenant_id_fkey FOREIGN KEY (tenant_id)
#         REFERENCES public.tenant (id) MATCH SIMPLE
#         ON UPDATE NO ACTION
#         ON DELETE RESTRICT,
#     CONSTRAINT product_check CHECK (requires_production = false OR requires_production = true AND current_stock IS NULL AND min_stock IS NULL AND replacement_cost IS NULL),
#     CONSTRAINT product_concept_check CHECK (concept = ANY (ARRAY[1, 2, 3])),
#     CONSTRAINT product_sale_price_check CHECK (sale_price >= 0::numeric),
#     CONSTRAINT product_sale_price_check1 CHECK (sale_price >= 0::numeric)
# )

# TABLESPACE pg_default;

# ALTER TABLE IF EXISTS public.product
#     OWNER to postgres;
