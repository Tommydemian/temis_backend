# Database Migrations

This directory contains all database schema migrations for the ERP system.

## Structure

```
migrations/
├── 001_create_enums.sql        # ENUM types
├── 002_create_tenant.sql       # Multi-tenancy
├── 003_create_customer.sql     # Customers
├── 004_create_product.sql      # Products
├── 005_create_order.sql        # Orders
├── 006_create_order_product.sql # Order line items
├── 007_create_invoice.sql      # AFIP invoices
├── run_all_migrations.sql      # Master script (runs all)
├── rollback_all.sql            # Rollback script (drops all)
└── README.md                   # This file
```

## Running Migrations

### Option 1: Run all migrations at once

```bash
cd migrations
psql -U postgres -d your_database -f run_all_migrations.sql
```

### Option 2: Run migrations individually

```bash
cd migrations
psql -U postgres -d your_database -f 001_create_enums.sql
psql -U postgres -d your_database -f 002_create_tenant.sql
# ... and so on
```

### Option 3: Using Python (asyncpg)

```python
import asyncpg
from pathlib import Path

async def run_migrations():
    conn = await asyncpg.connect('postgresql://postgres@localhost/your_database')
    
    migration_dir = Path('migrations')
    migration_files = sorted(migration_dir.glob('00*.sql'))
    
    for migration_file in migration_files:
        print(f'Running {migration_file.name}...')
        sql = migration_file.read_text()
        await conn.execute(sql)
        print(f'✓ Completed {migration_file.name}')
    
    await conn.close()
```

## Rollback (Drop All Tables)

**⚠️ WARNING: This will delete ALL data!**

```bash
cd migrations
psql -U postgres -d your_database -f rollback_all.sql
```

## Verifying Schema

After running migrations, verify the schema:

```bash
# Connect to database
psql -U postgres -d your_database

# List all tables
\dt

# List all ENUM types
\dT

# Describe a specific table
\d customer

# List all indexes
\di
```

## Key Design Decisions

### Multi-tenancy
- Every table has `tenant_id` for data isolation
- UNIQUE constraints are scoped per tenant
- ON DELETE RESTRICT prevents accidental data loss

### Snapshots
- `order_product` snapshots product data (price, name, IVA)
- `invoice` snapshots customer data (for AFIP compliance)
- Ensures historical accuracy even if master data changes

### Nullable Fields
- `order.customer_id` can be NULL (anonymous sales)
- `invoice` customer fields can be NULL (Factura C)
- `product` stock fields NULL if `requires_production = true`

### AFIP Compliance
- Invoice snapshots are immutable
- Supports Factura B and C
- Tracks CAE authorization codes
- $10M threshold logic handled in application layer

## Next Steps

After running migrations:
1. Run seed data (see `/seeds` directory)
2. Set up application connection pool
3. Implement business logic layer
4. Add data validation in application

## Troubleshooting

### "relation already exists"
You're trying to create tables that already exist. Run rollback first:
```bash
psql -U postgres -d your_database -f rollback_all.sql
```

### "must be owner of type"
You don't have permissions to drop ENUMs. Connect as superuser:
```bash
psql -U postgres -d your_database
```

### Foreign key violations
Make sure you run migrations in order. Use `run_all_migrations.sql` to ensure correct sequence.