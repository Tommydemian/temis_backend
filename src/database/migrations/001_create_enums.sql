-- ============================================
-- Migration: 001_create_enums.sql
-- Description: Create all ENUM types used across the schema
-- ============================================

-- Customer tax regime types
CREATE TYPE customer_tax_regime AS ENUM (
    'Monotributista',
    'Responsable Inscripto',
    'Consumidor Final',
    'Exento'
);

-- Order status
CREATE TYPE order_status AS ENUM (
    'pending',
    'confirmed',
    'in_production',
    'ready',
    'delivered',
    'cancelled'
);

-- Payment method
CREATE TYPE payment_method AS ENUM (
    'efectivo',
    'transferencia',
    'tarjeta',
    'otro'
);

-- Payment status
CREATE TYPE payment_status AS ENUM (
    'pending',
    'paid',
    'partial'
);

-- Delivery status
CREATE TYPE delivery_status AS ENUM (
    'pending',
    'dispatched',
    'delivered'
);

-- Order source/channel
CREATE TYPE order_source AS ENUM (
    'tiendanube',
    'whatsapp',
    'presencial',
    'manual'
);

-- Invoice type
CREATE TYPE invoice_type AS ENUM (
    'B',
    'C'
);

-- Invoice status
CREATE TYPE invoice_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'cancelled'
);