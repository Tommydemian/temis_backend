-- ============================================
-- Migration: 002_create_tenant.sql
-- Description: Create tenant table for multi-tenancy
-- ============================================

CREATE TABLE tenant (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE tenant IS 'Multi-tenancy: Each tenant represents a separate business/client';
COMMENT ON COLUMN tenant.name IS 'Business/company name';