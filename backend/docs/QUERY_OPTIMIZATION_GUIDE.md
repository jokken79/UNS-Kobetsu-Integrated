# Query Optimization Guide

## Performance Indexes Added in Migration 003

This guide explains how to leverage the performance indexes created in migration `003_add_performance_indexes.py` for optimal query performance.

## Index Usage Patterns

### 1. Status + Date Range Queries

**Index:** `ix_kobetsu_status_dates` (status, dispatch_start_date, dispatch_end_date)

**Optimized Query Example:**
```python
# Find active contracts expiring soon
from datetime import date, timedelta
from sqlalchemy import and_

expiring_soon = date.today() + timedelta(days=30)

contracts = db.query(KobetsuKeiyakusho)\
    .filter(and_(
        KobetsuKeiyakusho.status == 'active',
        KobetsuKeiyakusho.dispatch_end_date <= expiring_soon,
        KobetsuKeiyakusho.dispatch_end_date >= date.today()
    ))\
    .order_by(KobetsuKeiyakusho.dispatch_end_date)\
    .all()
```

### 2. Factory + Status Queries

**Index:** `ix_kobetsu_factory_status` (factory_id, status)

**Optimized Query Example:**
```python
# Get all active contracts for a specific factory
active_factory_contracts = db.query(KobetsuKeiyakusho)\
    .filter(and_(
        KobetsuKeiyakusho.factory_id == factory_id,
        KobetsuKeiyakusho.status == 'active'
    ))\
    .all()
```

### 3. Company + Plant + Status Queries

**Index:** `ix_kobetsu_company_plant_status` (company_id, plant_id, status)

**Optimized Query Example:**
```python
# Get active contracts for a specific company/plant (Base Madre integration)
contracts = db.query(KobetsuKeiyakusho)\
    .filter(and_(
        KobetsuKeiyakusho.company_id == company_id,
        KobetsuKeiyakusho.plant_id == plant_id,
        KobetsuKeiyakusho.status == 'active'
    ))\
    .all()
```

### 4. Recent Contracts Dashboard

**Index:** `ix_kobetsu_created_at` (created_at)

**Optimized Query Example:**
```python
# Get most recently created contracts
from datetime import datetime, timedelta

recent_contracts = db.query(KobetsuKeiyakusho)\
    .filter(KobetsuKeiyakusho.created_at >= datetime.now() - timedelta(days=7))\
    .order_by(KobetsuKeiyakusho.created_at.desc())\
    .limit(10)\
    .all()
```

### 5. Employee Assignment Date Queries

**Index:** `ix_kobetsu_employees_dates` (kobetsu_keiyakusho_id, individual_start_date, individual_end_date)

**Optimized Query Example:**
```python
# Find all employees assigned to a contract within a date range
employees = db.query(KobetsuEmployee)\
    .filter(and_(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
        KobetsuEmployee.individual_start_date <= end_date,
        KobetsuEmployee.individual_end_date >= start_date
    ))\
    .all()
```

### 6. Visa Expiry Monitoring

**Index:** `ix_employees_status_visa` (status, visa_expiry_date) - Partial index for active employees only

**Optimized Query Example:**
```python
# Find active employees with expiring visas
visa_warning_date = date.today() + timedelta(days=90)

expiring_visas = db.query(Employee)\
    .filter(and_(
        Employee.status == 'active',
        Employee.visa_expiry_date <= visa_warning_date,
        Employee.visa_expiry_date >= date.today()
    ))\
    .order_by(Employee.visa_expiry_date)\
    .all()
```

## Using the Materialized View

The materialized view `mv_active_contracts_summary` provides pre-computed results for complex queries involving active contracts.

### Refreshing the View
```sql
-- Refresh the materialized view (run periodically, e.g., via cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_active_contracts_summary;
```

### Query Example
```python
# Using raw SQL to query the materialized view
from sqlalchemy import text

result = db.execute(text("""
    SELECT * FROM mv_active_contracts_summary
    WHERE dispatch_end_date < :warning_date
    ORDER BY dispatch_end_date
"""), {"warning_date": date.today() + timedelta(days=30)})

expiring_contracts = result.fetchall()
```

## Query Optimization Tips

### 1. Use EXPLAIN ANALYZE

Always verify that your queries are using the intended indexes:

```python
from sqlalchemy import text

# Check query plan
explain = db.execute(text("""
    EXPLAIN ANALYZE
    SELECT * FROM kobetsu_keiyakusho
    WHERE status = 'active'
    AND dispatch_end_date <= :date
"""), {"date": date.today() + timedelta(days=30)})

for row in explain:
    print(row[0])
```

### 2. Leverage Partial Indexes

The partial indexes (`ix_employees_status_visa`, `ix_factory_lines_active`) only index rows matching the condition, making them smaller and faster:

```python
# This query uses the partial index efficiently
active_lines = db.query(FactoryLine)\
    .filter(and_(
        FactoryLine.factory_id == factory_id,
        FactoryLine.is_active == True  # Matches partial index condition
    ))\
    .all()
```

### 3. Batch Operations

For bulk operations, use batch inserts/updates:

```python
# Batch insert
db.bulk_insert_mappings(KobetsuEmployee, [
    {"kobetsu_keiyakusho_id": 1, "employee_id": 1, "hourly_rate": 1500},
    {"kobetsu_keiyakusho_id": 1, "employee_id": 2, "hourly_rate": 1600},
    # ...
])
db.commit()
```

### 4. Pagination for Large Results

Always paginate large result sets:

```python
def get_contracts_paginated(page: int, per_page: int = 20):
    return db.query(KobetsuKeiyakusho)\
        .filter(KobetsuKeiyakusho.status == 'active')\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
```

### 5. Use Eager Loading for Relationships

Prevent N+1 queries by eager loading relationships:

```python
from sqlalchemy.orm import joinedload

# Eager load related data
contracts = db.query(KobetsuKeiyakusho)\
    .options(
        joinedload(KobetsuKeiyakusho.factory),
        joinedload(KobetsuKeiyakusho.employees)
    )\
    .filter(KobetsuKeiyakusho.status == 'active')\
    .all()
```

## Monitoring Performance

### Check Index Usage
```sql
-- See which indexes are being used
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Find Slow Queries
```sql
-- Enable query logging for slow queries (> 100ms)
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

-- Check slow query log
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## Data Integrity Constraints

The migration also adds important check constraints:

1. **Company/Plant Consistency**: Ensures that if a plant_id is set, the corresponding company_id must also be set.
2. **Employee Assignment Dates**: Validates that individual_start_date <= individual_end_date.
3. **Rate Validation**: Ensures all rates (hourly, overtime, etc.) are non-negative.

These constraints prevent invalid data from being inserted, maintaining data quality at the database level.