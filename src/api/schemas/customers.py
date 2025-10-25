from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from src.api.schemas.invoices import CustomerTaxRegime


class CustomerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    tax_id_type: Optional[int] = None  # 80/86/96/99 etc.
    tax_id_number: Optional[str] = None

    tax_regime: Optional[CustomerTaxRegime] = None
    address: Optional[str] = None

    tenant_id: int


class Customer(CustomerBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


# CREATE TABLE IF NOT EXISTS public.customer
# (
#     id integer NOT NULL DEFAULT nextval('customer_id_seq'::regclass),
#     name character varying(255) COLLATE pg_catalog."default",
#     email character varying(255) COLLATE pg_catalog."default",
#     phone character varying(50) COLLATE pg_catalog."default",
#     tax_id_type integer,
#     tax_id_number character varying(11) COLLATE pg_catalog."default",
#     tax_regime customer_tax_regime,
#     address text COLLATE pg_catalog."default",
#     created_at timestamp with time zone DEFAULT now(),
#     updated_at timestamp with time zone,
#     tenant_id bigint,
#     CONSTRAINT customer_pkey PRIMARY KEY (id),
#     CONSTRAINT customer_tenant_id_email_key UNIQUE (tenant_id, email),
#     CONSTRAINT customer_tenant_id_tax_id_number_key UNIQUE (tenant_id, tax_id_number),
#     CONSTRAINT unique_tenant_phone UNIQUE (tenant_id, phone),
#     CONSTRAINT customer_tenant_id_fkey FOREIGN KEY (tenant_id)
#         REFERENCES public.tenant (id) MATCH SIMPLE
#         ON UPDATE NO ACTION
#         ON DELETE NO ACTION
# )

# TABLESPACE pg_default;

# ALTER TABLE IF EXISTS public.customer
#     OWNER to postgres;
