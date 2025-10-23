-- ============================================
-- Master Migration Script
-- Description: Runs all migrations in correct order
-- Usage: psql -U postgres -d your_database -f run_all_migrations.sql
-- ============================================

\echo '=========================================='
\echo 'Starting database schema creation...'
\echo '=========================================='

\echo ''
\echo '[1/7] Creating ENUM types...'
\i 001_create_enums.sql

\echo ''
\echo '[2/7] Creating tenant table...'
\i 002_create_tenant.sql

\echo ''
\echo '[3/7] Creating customer table...'
\i 003_create_customer.sql

\echo ''
\echo '[4/7] Creating product table...'
\i 004_create_product.sql

\echo ''
\echo '[5/7] Creating order table...'
\i 005_create_order.sql

\echo ''
\echo '[6/7] Creating order_product table...'
\i 006_create_order_product.sql

\echo ''
\echo '[7/7] Creating invoice table...'
\i 007_create_invoice.sql

\echo ''
\echo '=========================================='
\echo 'Schema creation completed successfully!'
\echo '=========================================='
\echo ''
\echo 'Next steps:'
\echo '1. Run seed data: psql -U postgres -d your_database -f seeds/seed_data.sql'
\echo '2. Verify tables: \dt'
\echo '3. Verify enums: \dT'