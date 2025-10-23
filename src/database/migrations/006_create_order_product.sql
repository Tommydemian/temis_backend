-- ============================================
-- Migration: 006_create_order_product.sql
-- Description: Create order_product junction table (order items)
-- ============================================

CREATE TABLE order_product (
    id SERIAL PRIMARY KEY,
    
    -- Relations
    order_id INTEGER NOT NULL REFERENCES "order"(id) ON DELETE RESTRICT,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
    
    -- Snapshot del producto al momento de la venta
    product_name VARCHAR(100) NOT NULL,
    unit_price NUMERIC(8,2) NOT NULL CHECK (unit_price >= 0),
    iva_rate NUMERIC(5,2) NOT NULL,
    
    -- Cantidad y descuentos
    quantity NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    discount_amount NUMERIC(8,2) DEFAULT 0 CHECK (discount_amount >= 0),
    
    -- Notas específicas del item
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Multi-tenancy
    tenant_id BIGINT NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
    
    -- Constraints: no duplicate products in same order
    UNIQUE(order_id, product_id)
);

-- Indexes
CREATE INDEX idx_order_product_order ON order_product(order_id);
CREATE INDEX idx_order_product_product ON order_product(product_id);
CREATE INDEX idx_order_product_tenant ON order_product(tenant_id);

-- Comments
COMMENT ON TABLE order_product IS 'Order line items - snapshots product data at time of sale';
COMMENT ON COLUMN order_product.product_name IS 'Snapshot: product name may change, this preserves historical value';
COMMENT ON COLUMN order_product.unit_price IS 'Snapshot: price at time of sale';
COMMENT ON COLUMN order_product.iva_rate IS 'Snapshot: IVA rate at time of sale';
COMMENT ON COLUMN order_product.discount_amount IS 'Discount in currency units (not percentage)';