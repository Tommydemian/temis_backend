-- ============================================
-- Migration: 003_create_customer.sql
-- Description: Create customer table with fiscal info
-- ============================================

CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    
    -- Basic info
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    
    -- Fiscal info (nullable until needed for invoicing)
    tax_id_type INT,  -- 80=CUIT, 86=CUIL, 96=DNI, 99=Consumidor Final
    tax_id_number VARCHAR(11),
    tax_regime customer_tax_regime,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Multi-tenancy
    tenant_id BIGINT NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
    
    -- Constraints: unique per tenant
    UNIQUE(tenant_id, email),
    UNIQUE(tenant_id, tax_id_number),
    UNIQUE(tenant_id, phone)
);

-- Indexes for common queries
CREATE INDEX idx_customer_tenant ON customer(tenant_id);
CREATE INDEX idx_customer_phone ON customer(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_customer_email ON customer(email) WHERE email IS NOT NULL;

-- Comments
COMMENT ON TABLE customer IS 'Customers/clients - can be created progressively (e.g., WhatsApp flow)';
COMMENT ON COLUMN customer.tax_id_type IS 'AFIP document type: 80=CUIT, 86=CUIL, 96=DNI, 99=Consumidor Final';
COMMENT ON COLUMN customer.tax_id_number IS 'Tax identification number (DNI or CUIT)';
COMMENT ON COLUMN customer.tax_regime IS 'Fiscal regime for AFIP invoicing logic';