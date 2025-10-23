-- ============================================
-- Seed Data Script
-- Description: Populate database with test data
-- Usage: psql -U postgres -d your_database -f seed_data.sql
-- ============================================

\echo '=========================================='
\echo 'Seeding database with test data...'
\echo '=========================================='

-- ============================================
-- 1. TENANTS
-- ============================================
\echo ''
\echo '[1/6] Inserting tenants...'

INSERT INTO tenant (id, name, created_at) VALUES
(1, 'Pastelería Dulce Sabor', NOW()),
(2, 'Panadería El Horno', NOW()),
(3, 'Repostería Gourmet', NOW());

-- Reset sequence
SELECT setval('tenant_id_seq', 3, true);

\echo '✓ Inserted 3 tenants'

-- ============================================
-- 2. CUSTOMERS
-- ============================================
\echo ''
\echo '[2/6] Inserting customers...'

-- Tenant 1 customers
INSERT INTO customer (name, email, phone, tax_id_type, tax_id_number, tax_regime, address, tenant_id) VALUES
('Juan Pérez', 'juan.perez@example.com', '1123456789', 96, '12345678', 'Consumidor Final', 'Av. Corrientes 1234, CABA', 1),
('María González', 'maria.gonzalez@example.com', '1198765432', 80, '20345678901', 'Monotributista', 'Calle Falsa 456, CABA', 1),
('Carlos Rodríguez', 'carlos@empresa.com', '1156781234', 80, '30123456789', 'Responsable Inscripto', 'San Martín 500, CABA', 1),
('Ana López', NULL, '1187654321', NULL, NULL, NULL, NULL, 1),  -- WhatsApp customer, minimal data
('Empresa ABC SA', 'contacto@abc.com', '1143218765', 80, '30987654321', 'Responsable Inscripto', 'Libertador 2000, CABA', 1);

-- Tenant 2 customers
INSERT INTO customer (name, email, phone, tax_id_type, tax_id_number, tax_regime, address, tenant_id) VALUES
('Pedro Martínez', 'pedro@example.com', '1122334455', 96, '87654321', 'Consumidor Final', 'Belgrano 123, Buenos Aires', 2),
('Laura Fernández', 'laura@example.com', '1155667788', 80, '27123456789', 'Monotributista', 'Rivadavia 800, Buenos Aires', 2);

\echo '✓ Inserted 7 customers across 2 tenants'

-- ============================================
-- 3. PRODUCTS
-- ============================================
\echo ''
\echo '[3/6] Inserting products...'

-- Tenant 1 products (Pastelería)
INSERT INTO product (name, description, sku, sale_price, category, iva_rate, requires_production, tenant_id) VALUES
('Torta de Chocolate', 'Torta casera de 1kg', 'TORTA-CHOC-1KG', 8500.00, 'Tortas', 21.00, true, 1),
('Torta de Frutilla', 'Torta con crema y frutillas frescas', 'TORTA-FRUT-1KG', 9000.00, 'Tortas', 21.00, true, 1),
('Brownie', 'Brownie con nueces (porción)', 'BROWNIE-PORCION', 1500.00, 'Pasteles', 21.00, true, 1),
('Velas Decorativas', 'Velas para tortas (pack x12)', 'VELAS-12', 800.00, 'Accesorios', 21.00, false, 1);

-- Update last product with stock info (purchased product)
UPDATE product 
SET current_stock = 50, min_stock = 10, purchase_price = 400.00
WHERE sku = 'VELAS-12' AND tenant_id = 1;

-- Tenant 2 products (Panadería)
INSERT INTO product (name, description, sku, sale_price, category, iva_rate, requires_production, tenant_id) VALUES
('Pan Francés', 'Pan francés tradicional', 'PAN-FRANC', 1200.00, 'Panes', 10.50, true, 2),
('Medialunas', 'Medialunas de manteca (docena)', 'MEDIA-DOC', 3500.00, 'Facturas', 10.50, true, 2),
('Café Molido', 'Café molido (500g)', 'CAFE-500G', 4500.00, 'Bebidas', 21.00, false, 2);

-- Update café with stock
UPDATE product 
SET current_stock = 20, min_stock = 5, purchase_price = 2800.00
WHERE sku = 'CAFE-500G' AND tenant_id = 2;

\echo '✓ Inserted 7 products (4 manufactured, 2 purchased with stock)'

-- ============================================
-- 4. ORDERS
-- ============================================
\echo ''
\echo '[4/6] Inserting orders...'

-- Tenant 1 orders
INSERT INTO "order" (customer_id, order_date, status, total_price, payment_method, payment_status, source, delivery_date, delivery_address, tenant_id) VALUES
(1, NOW() - INTERVAL '5 days', 'delivered', 8500.00, 'efectivo', 'paid', 'presencial', NOW() - INTERVAL '3 days', 'Av. Corrientes 1234, CABA', 1),
(2, NOW() - INTERVAL '3 days', 'in_production', 19500.00, 'transferencia', 'paid', 'whatsapp', NOW() + INTERVAL '2 days', 'Calle Falsa 456, CABA', 1),
(3, NOW() - INTERVAL '1 day', 'confirmed', 85000.00, 'transferencia', 'pending', 'tiendanube', NOW() + INTERVAL '5 days', 'San Martín 500, CABA', 1),
(NULL, NOW(), 'pending', 1500.00, 'efectivo', 'pending', 'presencial', NULL, NULL, 1);  -- Anonymous sale

-- Tenant 2 orders
INSERT INTO "order" (customer_id, order_date, status, total_price, payment_method, payment_status, source, tenant_id) VALUES
(6, NOW() - INTERVAL '2 days', 'delivered', 5200.00, 'efectivo', 'paid', 'presencial', 2),
(7, NOW(), 'pending', 12500.00, 'transferencia', 'pending', 'whatsapp', 2);

\echo '✓ Inserted 6 orders'

-- ============================================
-- 5. ORDER_PRODUCT (Order Items)
-- ============================================
\echo ''
\echo '[5/6] Inserting order items...'

-- Order 1: 1 Torta de Chocolate
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, tenant_id) VALUES
(1, 1, 'Torta de Chocolate', 8500.00, 21.00, 1, 1);

-- Order 2: 1 Torta de Chocolate + 1 Torta de Frutilla + 2 Brownies
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, tenant_id) VALUES
(2, 1, 'Torta de Chocolate', 8500.00, 21.00, 1, 1),
(2, 2, 'Torta de Frutilla', 9000.00, 21.00, 1, 1),
(2, 3, 'Brownie', 1500.00, 21.00, 2, 1);

-- Order 3: 10 Tortas de Chocolate (bulk order)
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, discount_amount, tenant_id) VALUES
(3, 1, 'Torta de Chocolate', 8500.00, 21.00, 10, 0, 1);

-- Order 4: 1 Brownie
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, tenant_id) VALUES
(4, 3, 'Brownie', 1500.00, 21.00, 1, 1);

-- Order 5 (Tenant 2): 3 Pan Francés + 2 Medialunas
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, tenant_id) VALUES
(5, 5, 'Pan Francés', 1200.00, 10.50, 3, 2),
(5, 6, 'Medialunas', 1400.00, 10.50, 2, 2);

-- Order 6 (Tenant 2): 2 Medialunas + 1 Café
INSERT INTO order_product (order_id, product_id, product_name, unit_price, iva_rate, quantity, tenant_id) VALUES
(6, 6, 'Medialunas', 3500.00, 10.50, 2, 2),
(6, 7, 'Café Molido', 4500.00, 21.00, 1, 2);

\echo '✓ Inserted 10 order items'

-- ============================================
-- 6. INVOICES
-- ============================================
\echo ''
\echo '[6/6] Inserting invoices...'

-- Order 1: Factura B (customer with DNI)
INSERT INTO invoice (
    order_id, invoice_type, point_of_sale, invoice_number, invoice_date,
    total_amount, net_amount, iva_amount,
    customer_name, customer_tax_id_type, customer_tax_id_number, customer_tax_regime, customer_address,
    status, cae, cae_expiration, tenant_id
) VALUES (
    1, 'B', 1, 1, CURRENT_DATE - 5,
    8500.00, 7024.79, 1475.21,
    'Juan Pérez', 96, '12345678', 'Consumidor Final', 'Av. Corrientes 1234, CABA',
    'approved', '12345678901234', CURRENT_DATE + 5, 1
);

-- Order 2: Factura B (monotributista)
INSERT INTO invoice (
    order_id, invoice_type, point_of_sale, invoice_number, invoice_date,
    total_amount, net_amount, iva_amount,
    customer_name, customer_tax_id_type, customer_tax_id_number, customer_tax_regime, customer_address,
    status, cae, cae_expiration, tenant_id
) VALUES (
    2, 'B', 1, 2, CURRENT_DATE - 3,
    19500.00, 16115.70, 3384.30,
    'María González', 80, '20345678901', 'Monotributista', 'Calle Falsa 456, CABA',
    'approved', '12345678901235', CURRENT_DATE + 7, 1
);

-- Order 3: Factura B (>$10M threshold - requires identification)
INSERT INTO invoice (
    order_id, invoice_type, point_of_sale, invoice_number, invoice_date,
    total_amount, net_amount, iva_amount,
    customer_name, customer_tax_id_type, customer_tax_id_number, customer_tax_regime, customer_address,
    status, cae, cae_expiration, tenant_id
) VALUES (
    3, 'B', 1, 3, CURRENT_DATE - 1,
    85000.00, 70247.93, 14752.07,
    'Empresa ABC SA', 80, '30987654321', 'Responsable Inscripto', 'Libertador 2000, CABA',
    'approved', '12345678901236', CURRENT_DATE + 9, 1
);

-- Order 4: Factura C (anonymous sale, small amount)
INSERT INTO invoice (
    order_id, invoice_type, point_of_sale, invoice_number, invoice_date,
    total_amount, net_amount, iva_amount,
    status, tenant_id
) VALUES (
    4, 'C', 1, 4, CURRENT_DATE,
    1500.00, 1239.67, 260.33,
    'pending', 1
);

-- Tenant 2 invoice
INSERT INTO invoice (
    order_id, invoice_type, point_of_sale, invoice_number, invoice_date,
    total_amount, net_amount, iva_amount,
    customer_name, customer_tax_id_type, customer_tax_id_number, customer_tax_regime, customer_address,
    status, cae, cae_expiration, tenant_id
) VALUES (
    5, 'B', 1, 1, CURRENT_DATE - 2,
    5200.00, 4561.40, 638.60,
    'Pedro Martínez', 96, '87654321', 'Consumidor Final', 'Belgrano 123, Buenos Aires',
    'approved', '98765432109876', CURRENT_DATE + 8, 2
);

\echo '✓ Inserted 5 invoices (4 approved, 1 pending)'

\echo ''
\echo '=========================================='
\echo 'Seed data inserted successfully!'
\echo '=========================================='
\echo ''
\echo 'Summary:'
\echo '  - 3 tenants'
\echo '  - 7 customers'
\echo '  - 7 products (4 manufactured, 3 purchased)'
\echo '  - 6 orders'
\echo '  - 10 order items'
\echo '  - 5 invoices'
\echo ''
\echo 'Try these queries:'
\echo '  SELECT * FROM customer WHERE tenant_id = 1;'
\echo '  SELECT * FROM "order" WHERE status = ''pending'';'
\echo '  SELECT * FROM invoice WHERE status = ''approved'';'