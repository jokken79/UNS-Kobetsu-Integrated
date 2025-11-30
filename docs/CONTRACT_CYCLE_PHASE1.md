# Contract Cycle Configuration - Phase 1 Implementation

## Overview
Phase 1 adds the database schema and models to support factory-specific contract renewal cycles. This implementation provides the foundation for automatic contract renewal detection and notification.

## Database Changes

### 1. Migration: `004_add_contract_cycle_fields`
Located at: `/backend/alembic/versions/004_add_contract_cycle_fields.py`

#### New Fields Added to `factories` Table:
- **`contract_cycle_type`** (ENUM: 'monthly', 'annual')
  - Default: 'annual'
  - Determines whether contracts renew monthly or annually

- **`cycle_day_type`** (ENUM: 'fixed', 'month_end')
  - Default: 'fixed'
  - Controls whether renewal happens on a specific date or month-end

- **`fiscal_year_end_month`** (INTEGER: 1-12)
  - Default: 3 (March)
  - The fiscal year ending month for the factory

- **`fiscal_year_end_day`** (INTEGER: 1-31)
  - Default: 31
  - The fiscal year ending day

- **`contract_renewal_days_before`** (INTEGER: 0-365)
  - Default: 30
  - Number of days before contract end to trigger renewal notification

#### New Field Added to `kobetsu_keiyakusho` Table:
- **`previous_contract_id`** (INTEGER, nullable)
  - Foreign key to self (kobetsu_keiyakusho.id)
  - Tracks contract renewal chains
  - Allows navigation from renewed contracts to their predecessors

#### Data Migration for Known Factories:
- **Misuzu factories**: Set to monthly cycle, month-end, September fiscal year
- **Takao factories**: Set to annual cycle, fixed date, September 30

## Model Updates

### Factory Model (`/backend/app/models/factory.py`)
- Added `ContractCycleType` enum class
- Added `ContractCycleDayType` enum class
- Added 5 new columns with appropriate types and defaults
- Added check constraints for data validation:
  - `fiscal_year_end_month` BETWEEN 1 AND 12
  - `fiscal_year_end_day` BETWEEN 1 AND 31
  - `contract_renewal_days_before` BETWEEN 0 AND 365

### KobetsuKeiyakusho Model (`/backend/app/models/kobetsu_keiyakusho.py`)
- Added `previous_contract_id` column with foreign key to self
- Added self-referential relationship for contract renewal tracking
- Indexed for efficient renewal chain queries

## Schema Updates

### Factory Schemas (`/backend/app/schemas/factory.py`)
- Added `ContractCycleTypeEnum` and `ContractCycleDayTypeEnum` enums
- Added new fields to `FactoryBase` with defaults and validation
- Added validators for:
  - `fiscal_year_end_month`: Must be 1-12
  - `fiscal_year_end_day`: Must be 1-31, with month-specific validation
  - `contract_renewal_days_before`: Must be 0-365
- Updated `FactoryUpdate` to allow modification of cycle settings

### KobetsuKeiyakusho Schemas (`/backend/app/schemas/kobetsu_keiyakusho.py`)
- Added `previous_contract_id` to:
  - `KobetsuKeiyakushoCreate`: For creating renewed contracts
  - `KobetsuKeiyakushoUpdate`: For updating renewal links
  - `KobetsuKeiyakushoResponse`: For displaying renewal chains

## Usage Examples

### Setting Factory Contract Cycle Configuration
```python
# Create factory with monthly renewal cycle (Misuzu example)
factory_data = {
    "company_name": "Misuzu Corporation",
    "plant_name": "Main Plant",
    "contract_cycle_type": "monthly",
    "cycle_day_type": "month_end",
    "fiscal_year_end_month": 9,  # September
    "fiscal_year_end_day": 30,
    "contract_renewal_days_before": 30
}

# Create factory with annual cycle (Takao example)
factory_data = {
    "company_name": "Takao Industries",
    "plant_name": "Factory A",
    "contract_cycle_type": "annual",
    "cycle_day_type": "fixed",
    "fiscal_year_end_month": 9,
    "fiscal_year_end_day": 30,
    "contract_renewal_days_before": 30
}
```

### Creating a Renewed Contract
```python
# When renewing a contract, link to previous
renewed_contract = {
    "factory_id": 1,
    "previous_contract_id": 123,  # ID of expiring contract
    "dispatch_start_date": "2025-01-01",
    "dispatch_end_date": "2025-12-31",
    # ... other contract fields
}
```

## Migration Commands

```bash
# Apply the migration
docker exec -it uns-kobetsu-backend alembic upgrade head

# Rollback if needed
docker exec -it uns-kobetsu-backend alembic downgrade -1

# View migration history
docker exec -it uns-kobetsu-backend alembic history

# Check current version
docker exec -it uns-kobetsu-backend alembic current
```

## Testing

### Verify Migration Syntax
```bash
cd backend
python scripts/validate_migration_syntax.py
```

### Test Through API (after migration)
```bash
# Get factory with cycle configuration
curl -X GET http://localhost:8010/api/v1/factories/1

# Update factory cycle settings
curl -X PUT http://localhost:8010/api/v1/factories/1 \
  -H "Content-Type: application/json" \
  -d '{
    "contract_cycle_type": "monthly",
    "cycle_day_type": "month_end",
    "fiscal_year_end_month": 9,
    "fiscal_year_end_day": 30
  }'
```

## Next Steps (Phase 2)

Phase 2 will add the business logic to use these configuration fields:

1. **Contract Renewal Service**
   - Calculate next renewal date based on factory settings
   - Detect contracts approaching renewal
   - Generate renewal notifications

2. **API Endpoints**
   - `GET /api/v1/contracts/expiring` - List contracts needing renewal
   - `POST /api/v1/contracts/{id}/renew` - Create renewal from existing contract

3. **Frontend Updates**
   - Factory configuration UI for cycle settings
   - Contract renewal workflow
   - Renewal notification display

## File Paths

All modified files (absolute paths):
- `/home/user/UNS-Kobetsu-Integrated/backend/alembic/versions/004_add_contract_cycle_fields.py`
- `/home/user/UNS-Kobetsu-Integrated/backend/app/models/factory.py`
- `/home/user/UNS-Kobetsu-Integrated/backend/app/models/kobetsu_keiyakusho.py`
- `/home/user/UNS-Kobetsu-Integrated/backend/app/schemas/factory.py`
- `/home/user/UNS-Kobetsu-Integrated/backend/app/schemas/kobetsu_keiyakusho.py`

Validation scripts:
- `/home/user/UNS-Kobetsu-Integrated/backend/scripts/validate_migration_syntax.py`
- `/home/user/UNS-Kobetsu-Integrated/backend/scripts/test_migration.py`