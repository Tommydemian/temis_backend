-- ============================================
-- Rollback Script
-- Description: Drops all tables and ENUMs in reverse order
-- WARNING: This will DELETE ALL DATA!
-- Usage: psql -U postgres -d your_database -f rollback_all.sql
-- ============================================

\echo '=========================================='
\echo 'WARNING: This will DROP all tables and data!'
\echo '=========================================='
\echo 'Press Ctrl+C to cancel, or press Enter to continue...'
\prompt 'Continue? (yes/no): ' confirm

-- Drop tables in reverse order (respecting foreign key dependencies)
\echo ''
\echo 'Dropping tables...'

DROP TABLE IF EXISTS invoice CASCADE;
\echo '✓ Dropped invoice'

DROP TABLE IF EXISTS order_product CASCADE;
\echo '✓ Dropped order_product'

DROP TABLE IF EXISTS "order" CASCADE;
\echo '✓ Dropped order'

DROP TABLE IF EXISTS product CASCADE;
\echo '✓ Dropped product'

DROP TABLE IF EXISTS customer CASCADE;
\echo '✓ Dropped customer'

DROP TABLE IF EXISTS tenant CASCADE;
\echo '✓ Dropped tenant'

-- Drop ENUMs
\echo ''
\echo 'Dropping ENUM types...'

DROP TYPE IF EXISTS invoice_status CASCADE;
DROP TYPE IF EXISTS invoice_type CASCADE;
DROP TYPE IF EXISTS order_source CASCADE;
DROP TYPE IF EXISTS delivery_status CASCADE;
DROP TYPE IF EXISTS payment_status CASCADE;
DROP TYPE IF EXISTS payment_method CASCADE;
DROP TYPE IF EXISTS order_status CASCADE;
DROP TYPE IF EXISTS customer_tax_regime CASCADE;

\echo '✓ Dropped all ENUMs'

\echo ''
\echo '=========================================='
\echo 'Rollback completed!'
\echo '=========================================='