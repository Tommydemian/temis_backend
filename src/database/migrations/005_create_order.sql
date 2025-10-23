-- ============================================
-- Migration: 005_create_order.sql
-- Description: Create order table
-- ============================================

CREATE TABLE "order" (
    id SERIAL PRIMARY KEY,
    
    -- Customer relation (nullable for anonymous sales)
    customer_id INTEGER REFERENCES customer(id) ON DELETE RESTRICT,
    
    -- Order info
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status order_status DEFAULT 'pending',
    total_price NUMERIC(8,2) NOT NULL CHECK (total_price > 0),
    notes TEXT,
    
    -- Payment
    payment_method payment_method,
    payment_status payment_status DEFAULT 'pending',
    payment_date TIMESTAMP WITH TIME ZONE,
    
    -- Source/channel
    source order_source,
    
    -- Delivery
    delivery_date TIMESTAMP WITH TIME ZONE,
    delivery_address TEXT,
    delivery_status delivery_status,
    delivery_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Multi-tenancy
    tenant_id BIGINT NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT
);

-- Indexes for common queries
CREATE INDEX idx_order_tenant ON "order"(tenant_id);
CREATE INDEX idx_order_customer ON "order"(customer_id) WHERE customer_id IS NOT NULL;
CREATE INDEX idx_order_status ON "order"(tenant_id, status);
CREATE INDEX idx_order_date ON "order"(tenant_id, order_date DESC);
CREATE INDEX idx_order_payment_status ON "order"(tenant_id, payment_status);

-- Comments
COMMENT ON TABLE "order" IS 'Customer orders - can be anonymous (customer_id NULL) for quick sales';
COMMENT ON COLUMN "order".customer_id IS 'NULL allowed for anonymous sales without customer registration';
COMMENT ON COLUMN "order".source IS 'Sales channel: whatsapp, tiendanube, presencial, manual';
COMMENT ON COLUMN "order".delivery_status IS 'NULL if no delivery needed (e.g., pickup)';