# ERP Database Schema - Complete Documentation

## Overview

This database schema is designed for a **multi-tenant ERP system** targeting **monotributistas (sole proprietors)** in Argentina. The system handles:

- Customer management (with progressive data capture)
- Product catalog (manufactured vs purchased)
- Order processing (multiple sales channels)
- AFIP-compliant invoicing (Factura B and C)

---

## Architecture Decisions

### Multi-tenancy
- Every table includes `tenant_id` for data isolation
- UNIQUE constraints are scoped per tenant
- `ON DELETE RESTRICT` prevents accidental cascading deletes

### Immutable Snapshots
- `order_product` snapshots product data at time of sale
- `invoice` snapshots customer data for AFIP compliance
- Historical accuracy preserved even if master data changes

### Progressive Data Capture
- `order.customer_id` can be NULL (anonymous sales)
- `customer` fields are mostly nullable (can be completed over time)
- Supports WhatsApp flow: phone → full profile → invoicing

### AFIP Compliance
- Invoice types: B (identified customer) and C (anonymous)
- $10M threshold logic (handled in application layer)
- CAE authorization tracking
- Immutable customer snapshots in invoices

---

## Database Schema

### ENUMs

```sql
customer_tax_regime: 'Monotributista' | 'Responsable Inscripto' | 'Consumidor Final' | 'Exento'
order_status: 'pending' | 'confirmed' | 'in_production' | 'ready' | 'delivered' | 'cancelled'
payment_method: 'efectivo' | 'transferencia' | 'tarjeta' | 'otro'
payment_status: 'pending' | 'paid' | 'partial'
delivery_status: 'pending' | 'dispatched' | 'delivered'
order_source: 'tiendanube' | 'whatsapp' | 'presencial' | 'manual'
invoice_type: 'B' | 'C'
invoice_status: 'pending' | 'approved' | 'rejected' | 'cancelled'
```

### Entity Relationships

```
tenant (1) ──→ (N) customer
tenant (1) ──→ (N) product
tenant (1) ──→ (N) order
tenant (1) ──→ (N) invoice

customer (1) ──→ (N) order  [nullable - allows anonymous orders]
order (1) ──→ (N) order_product
order (1) ──→ (N) invoice
product (1) ──→ (N) order_product
```

---

## Tables

### 1. tenant
Multi-tenancy parent table. Each tenant is an independent business.

**Key Fields:**
- `id` (bigserial, PK)
- `name` (varchar, business name)

**Notes:**
- Central to all data isolation
- Cannot be deleted if has related data (RESTRICT)

---

### 2. customer
Stores customer/client information. Supports progressive data capture.

**Key Fields:**
- `id` (serial, PK)
- `name`, `email`, `phone`, `address` (all nullable)
- `tax_id_type` (int: 80=CUIT, 86=CUIL, 96=DNI, 99=Consumidor Final)
- `tax_id_number` (varchar(11))
- `tax_regime` (enum: determines invoicing logic)
- `tenant_id` (FK, NOT NULL)

**Unique Constraints:**
- `(tenant_id, email)`
- `(tenant_id, tax_id_number)`
- `(tenant_id, phone)`

**Use Cases:**
- WhatsApp: Create with phone only, complete later
- Tienda Nube: Create with full data from webhook
- Presencial: Create when invoicing is needed

---

### 3. product
Product catalog. Distinguishes manufactured vs purchased items.

**Key Fields:**
- `id` (serial, PK)
- `name`, `description`, `sku`, `category`
- `sale_price` (numeric, NOT NULL)
- `purchase_price` (numeric, only for purchased products)
- `iva_rate` (numeric, default 21.00)
- `current_stock`, `min_stock` (only for purchased products)
- `requires_production` (boolean)
- `is_active` (boolean)
- `tenant_id` (FK, NOT NULL)

**Unique Constraints:**
- `(tenant_id, sku)`

**CHECK Constraints:**
- If `requires_production = true`, then stock fields must be NULL

**Logic:**
- `requires_production = true`: Manufactured product (needs BOM, no stock tracking)
- `requires_production = false`: Purchased product (has stock, purchase price)

---

### 4. order
Customer orders from multiple channels.

**Key Fields:**
- `id` (serial, PK)
- `customer_id` (FK, **nullable** for anonymous sales)
- `order_date` (timestamp, default NOW())
- `status` (enum, default 'pending')
- `total_price` (numeric, NOT NULL, > 0)
- `notes` (text)
- **Payment fields:** `payment_method`, `payment_status`, `payment_date`
- **Source:** `source` (enum: channel)
- **Delivery:** `delivery_date`, `delivery_address`, `delivery_status`, `delivery_notes`
- `tenant_id` (FK, NOT NULL)

**Indexes:**
- `tenant_id`, `customer_id`, `status`, `order_date`, `payment_status`

**Use Cases:**
- Presencial anonymous: `customer_id = NULL`
- WhatsApp: `source = 'whatsapp'`, may start without customer
- Tienda Nube: `source = 'tiendanube'`, customer always linked

---

### 5. order_product
Junction table. Order line items with product snapshots.

**Key Fields:**
- `id` (serial, PK)
- `order_id` (FK, NOT NULL)
- `product_id` (FK, NOT NULL)
- **Snapshots:** `product_name`, `unit_price`, `iva_rate` (at time of sale)
- `quantity` (numeric, > 0)
- `discount_amount` (numeric, >= 0)
- `notes` (text, item-specific notes)
- `tenant_id` (FK, NOT NULL)

**Unique Constraints:**
- `(order_id, product_id)` - no duplicate products per order

**Purpose:**
- Snapshot preserves historical pricing
- Quantity can be decimal (e.g., 2.5 kg)
- Discount in currency units (not percentage)

---

### 6. invoice
AFIP invoices. Immutable customer snapshots for compliance.

**Key Fields:**
- `id` (serial, PK)
- `order_id` (FK, NOT NULL)
- `invoice_type` (enum: 'B' or 'C')
- `point_of_sale`, `invoice_number` (int)
- `invoice_date` (date)
- **AFIP response:** `cae` (varchar(14)), `cae_expiration` (date)
- **Amounts:** `total_amount`, `net_amount`, `iva_amount`
- **Customer snapshot (nullable for Factura C):**
  - `customer_name`, `customer_tax_id_type`, `customer_tax_id_number`
  - `customer_tax_regime`, `customer_address`, `customer_phone`, `customer_email`
- `status` (enum, default 'pending')
- `afip_error_message` (text)
- `tenant_id` (FK, NOT NULL)

**Unique Constraints:**
- `(tenant_id, point_of_sale, invoice_number)`

**Invoice Logic:**
- **Factura B:** Customer identified (has tax_id)
- **Factura C:** Anonymous consumer (customer fields NULL)
- **$10M threshold:** If total >= $10M, must use Factura B with full identification

**Snapshot Purpose:**
- Customer data frozen at time of invoicing
- Changes to customer table don't affect historical invoices
- AFIP compliance requires immutable records

---

## Business Flows

### Flow 1: WhatsApp Sale

```
1. Message arrives → Webhook triggered
2. get_wspp_user(phone) → Search/create customer
3. User manually creates order in ERP
4. If customer requests invoice:
   - Collect tax_id if needed
   - Create invoice with customer snapshot
5. Otherwise: Factura C (anonymous)
```

### Flow 2: Presencial Sale

```
1. Customer walks in
2. Process sale:
   - Small amount, no invoice → order with customer_id = NULL
   - Needs invoice → Create customer, then order, then invoice B
3. If total >= $10M → MUST identify customer (Factura B)
```

### Flow 3: Tienda Nube Integration

```
1. Webhook receives order
2. Search customer by email/phone
3. If not exists → Create customer with full data
4. Create order (linked to customer)
5. Generate invoice (B or C based on customer data)
```

---

## AFIP Invoicing Rules

### Factura B (Identified)
**When to use:**
- Customer has tax_id (DNI or CUIT)
- Total amount >= $10,000,000 (mandatory identification)
- Customer explicitly requests invoice

**Required fields:**
- customer_name
- customer_tax_id_type + customer_tax_id_number
- customer_address (if >= $10M)

### Factura C (Anonymous)
**When to use:**
- Small consumer sales (< $10M)
- Customer doesn't want/need invoice
- Quick presencial sales

**Required fields:**
- None (all customer fields NULL)

---

## Indexes Strategy

**Performance-critical indexes:**
- `customer(tenant_id, phone)` - WhatsApp lookups
- `order(tenant_id, order_date DESC)` - Recent orders
- `order(tenant_id, status)` - Order management
- `invoice(tenant_id, status)` - Pending invoices
- `product(tenant_id, is_active)` - Active catalog

**Partial indexes (WHERE clauses):**
- `customer(phone) WHERE phone IS NOT NULL`
- `customer(email) WHERE email IS NOT NULL`

---

## Migration Instructions

### Setup
```bash
# 1. Create database
createdb your_database

# 2. Run all migrations
cd migrations
psql -U postgres -d your_database -f run_all_migrations.sql

# 3. Load seed data (optional)
psql -U postgres -d your_database -f seed_data.sql

# 4. Verify
psql -U postgres -d your_database -c "\dt"
```

### Rollback
```bash
psql -U postgres -d your_database -f rollback_all.sql
```

---

## Future Enhancements

### Phase 2: Manufacturing
- Full BOM (bill_of_materials) implementation
- Component inventory tracking
- Production scheduling

### Phase 3: Advanced Features
- Nota de crédito (credit notes)
- Factura A support (RI → RI)
- Multi-warehouse inventory
- Payment plans / installments

### Phase 4: Analytics
- Sales reports by channel
- Customer lifetime value
- Product profitability analysis
- AFIP compliance dashboard

---

## Testing Queries

```sql
-- Test multi-tenancy isolation
SELECT COUNT(*) FROM customer WHERE tenant_id = 1;
SELECT COUNT(*) FROM customer WHERE tenant_id = 2;

-- Test anonymous orders
SELECT * FROM "order" WHERE customer_id IS NULL;

-- Test invoices by type
SELECT invoice_type, COUNT(*) FROM invoice GROUP BY invoice_type;

-- Test manufactured vs purchased products
SELECT requires_production, COUNT(*) FROM product GROUP BY requires_production;

-- Test order with items and invoice
SELECT 
  o.id as order_id,
  o.total_price,
  c.name as customer_name,
  i.invoice_type,
  i.cae
FROM "order" o
LEFT JOIN customer c ON o.customer_id = c.id
LEFT JOIN invoice i ON o.id = i.order_id
WHERE o.tenant_id = 1
ORDER BY o.order_date DESC;
```

---

## Contact & Support

For questions or issues with the schema:
1. Review the README.md in migrations folder
2. Check seed_data.sql for usage examples
3. Consult AFIP documentation for invoicing rules

---

**Schema Version:** 1.0.0  
**Last Updated:** October 2025  
**Target:** Monotributistas, Argentina