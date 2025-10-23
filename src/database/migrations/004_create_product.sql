-- ============================================
-- Migration: 004_create_product.sql
-- Description: Create product table
-- ============================================

CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sku VARCHAR(50),
    category VARCHAR(50),
    
    -- Pricing
    sale_price NUMERIC(8,2) NOT NULL CHECK (sale_price >= 0),
    purchase_price NUMERIC(8,2),  -- Only for requires_production = false
    iva_rate NUMERIC(5,2) DEFAULT 21.00,
    
    -- Stock management (only for requires_production = false)
    current_stock NUMERIC(10,2),
    min_stock NUMERIC(10,2),
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    requires_production BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Multi-tenancy
    tenant_id BIGINT NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
    
    -- Constraints
    UNIQUE(tenant_id, sku),
    
    -- Logic: if requires_production = true, stock fields must be NULL
    CHECK (
        (requires_production = false) OR 
        (requires_production = true AND current_stock IS NULL AND min_stock IS NULL AND purchase_price IS NULL)
    )
);

-- Indexes
CREATE INDEX idx_product_tenant ON product(tenant_id);
CREATE INDEX idx_product_active ON product(tenant_id, is_active);
CREATE INDEX idx_product_category ON product(tenant_id, category) WHERE category IS NOT NULL;

-- Comments
COMMENT ON TABLE product IS 'Products - can be purchased for resale or manufactured';
COMMENT ON COLUMN product.requires_production IS 'true = manufactured (needs BOM), false = purchased for resale';
COMMENT ON COLUMN product.current_stock IS 'Current stock level (only for purchased products)';
COMMENT ON COLUMN product.min_stock IS 'Minimum stock alert threshold (only for purchased products)';
COMMENT ON COLUMN product.purchase_price IS 'Cost price for purchased products';