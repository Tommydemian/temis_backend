-- ============================================
-- Migration: 007_create_invoice.sql
-- Description: Create invoice table for AFIP billing
-- ============================================

CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    
    -- Order relation
    order_id INTEGER NOT NULL REFERENCES "order"(id) ON DELETE RESTRICT,
    
    -- Invoice info
    invoice_type invoice_type NOT NULL,
    point_of_sale INTEGER NOT NULL,
    invoice_number INTEGER NOT NULL,
    invoice_date DATE NOT NULL,
    
    -- AFIP response
    cae VARCHAR(14),  -- CAE (Código de Autorización Electrónico)
    cae_expiration DATE,
    
    -- Amounts
    total_amount NUMERIC(15,2) NOT NULL CHECK (total_amount > 0),
    net_amount NUMERIC(15,2) NOT NULL CHECK (net_amount >= 0),
    iva_amount NUMERIC(15,2) NOT NULL CHECK (iva_amount >= 0),
    
    -- Customer snapshot (nullable for Factura C)
    customer_name VARCHAR(255),
    customer_tax_id_type INT,  -- 80=CUIT, 86=CUIL, 96=DNI, 99=Consumidor Final
    customer_tax_id_number VARCHAR(11),
    customer_tax_regime customer_tax_regime,
    customer_address TEXT,
    customer_phone VARCHAR(50),
    customer_email VARCHAR(255),
    
    -- Status & errors
    status invoice_status DEFAULT 'pending',
    afip_error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Multi-tenancy
    tenant_id BIGINT NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
    
    -- Constraints: unique invoice number per point of sale per tenant
    UNIQUE(tenant_id, point_of_sale, invoice_number)
);

-- Indexes for common queries
CREATE INDEX idx_invoice_tenant ON invoice(tenant_id);
CREATE INDEX idx_invoice_order ON invoice(order_id);
CREATE INDEX idx_invoice_status ON invoice(tenant_id, status);
CREATE INDEX idx_invoice_date ON invoice(tenant_id, invoice_date DESC);
CREATE INDEX idx_invoice_cae ON invoice(cae) WHERE cae IS NOT NULL;
CREATE INDEX idx_invoice_customer_tax_id ON invoice(tenant_id, customer_tax_id_number) WHERE customer_tax_id_number IS NOT NULL;

-- Comments
COMMENT ON TABLE invoice IS 'AFIP invoices - immutable snapshots of customer data at time of billing';
COMMENT ON COLUMN invoice.invoice_type IS 'B = Factura B, C = Factura C';
COMMENT ON COLUMN invoice.cae IS 'AFIP authorization code - NULL until approved';
COMMENT ON COLUMN invoice.customer_name IS 'Snapshot: NULL for Factura C (Consumidor Final sin identificar)';
COMMENT ON COLUMN invoice.customer_tax_id_type IS 'Snapshot: AFIP document type at time of invoicing';
COMMENT ON COLUMN invoice.status IS 'pending = awaiting AFIP, approved = CAE received, rejected = AFIP error, cancelled = anulada';