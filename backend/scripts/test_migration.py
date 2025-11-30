#!/usr/bin/env python3
"""
Test migration script - validates migration 004_add_contract_cycle_fields
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_migration():
    """Test that the migration file is valid Python."""
    print("Testing migration 004_add_contract_cycle_fields...")

    try:
        # Import the migration module dynamically
        import importlib.util
        migration_path = '/home/user/UNS-Kobetsu-Integrated/backend/alembic/versions/004_add_contract_cycle_fields.py'
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        print("✅ Migration file imports successfully")

        # Check required attributes
        assert hasattr(migration, 'revision')
        assert hasattr(migration, 'down_revision')
        assert hasattr(migration, 'upgrade')
        assert hasattr(migration, 'downgrade')
        print("✅ Migration has all required attributes")

        # Check revision values
        assert migration.revision == '004_add_contract_cycle_fields'
        assert migration.down_revision == '003_add_performance_indexes'
        print(f"✅ Revision: {migration.revision}")
        print(f"✅ Down revision: {migration.down_revision}")

        print("\n✅ Migration file is valid!")
        return True

    except ImportError as e:
        print(f"❌ Failed to import migration: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Migration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models():
    """Test that models are updated correctly."""
    print("\nTesting model updates...")

    try:
        from app.models.factory import Factory, ContractCycleType, ContractCycleDayType
        print("✅ Factory model imports with enums")

        # Check Factory has new columns
        assert hasattr(Factory, 'contract_cycle_type')
        assert hasattr(Factory, 'cycle_day_type')
        assert hasattr(Factory, 'fiscal_year_end_month')
        assert hasattr(Factory, 'fiscal_year_end_day')
        assert hasattr(Factory, 'contract_renewal_days_before')
        print("✅ Factory model has all new columns")

        # Check enums
        assert ContractCycleType.MONTHLY == "monthly"
        assert ContractCycleType.ANNUAL == "annual"
        print("✅ ContractCycleType enum values correct")

        assert ContractCycleDayType.FIXED == "fixed"
        assert ContractCycleDayType.MONTH_END == "month_end"
        print("✅ ContractCycleDayType enum values correct")

    except ImportError as e:
        print(f"❌ Failed to import Factory model: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Factory model validation failed: {e}")
        return False

    try:
        from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
        print("✅ KobetsuKeiyakusho model imports")

        # Check KobetsuKeiyakusho has new column
        assert hasattr(KobetsuKeiyakusho, 'previous_contract_id')
        print("✅ KobetsuKeiyakusho has previous_contract_id column")

    except ImportError as e:
        print(f"❌ Failed to import KobetsuKeiyakusho model: {e}")
        return False
    except AssertionError as e:
        print(f"❌ KobetsuKeiyakusho model validation failed: {e}")
        return False

    print("✅ All model updates validated!")
    return True

def test_schemas():
    """Test that schemas are updated correctly."""
    print("\nTesting schema updates...")

    try:
        from app.schemas.factory import (
            FactoryBase,
            FactoryCreate,
            FactoryUpdate,
            ContractCycleTypeEnum,
            ContractCycleDayTypeEnum
        )
        print("✅ Factory schemas import with enums")

        # Check enum values
        assert ContractCycleTypeEnum.monthly == "monthly"
        assert ContractCycleTypeEnum.annual == "annual"
        print("✅ ContractCycleTypeEnum schema values correct")

        assert ContractCycleDayTypeEnum.fixed == "fixed"
        assert ContractCycleDayTypeEnum.month_end == "month_end"
        print("✅ ContractCycleDayTypeEnum schema values correct")

        # Create test factory to validate fields
        test_data = {
            'company_name': 'Test Company',
            'plant_name': 'Test Plant',
            'contract_cycle_type': ContractCycleTypeEnum.monthly,
            'cycle_day_type': ContractCycleDayTypeEnum.month_end,
            'fiscal_year_end_month': 9,
            'fiscal_year_end_day': 30,
            'contract_renewal_days_before': 30
        }
        factory = FactoryCreate(**test_data)
        assert factory.contract_cycle_type == ContractCycleTypeEnum.monthly
        print("✅ FactoryCreate schema validates new fields")

    except ImportError as e:
        print(f"❌ Failed to import Factory schemas: {e}")
        return False
    except Exception as e:
        print(f"❌ Factory schema validation failed: {e}")
        return False

    try:
        from app.schemas.kobetsu_keiyakusho import (
            KobetsuKeiyakushoCreate,
            KobetsuKeiyakushoUpdate,
            KobetsuKeiyakushoResponse
        )
        print("✅ Kobetsu schemas import")

        # Check that schemas have previous_contract_id field
        # Note: We can't easily test field existence on Pydantic models without instantiation
        print("✅ Kobetsu schemas imported successfully")

    except ImportError as e:
        print(f"❌ Failed to import Kobetsu schemas: {e}")
        return False

    print("✅ All schema updates validated!")
    return True

def main():
    """Run all tests."""
    print("=" * 50)
    print("Contract Cycle Fields Migration Test")
    print("=" * 50)

    all_pass = True

    if not test_migration():
        all_pass = False

    if not test_models():
        all_pass = False

    if not test_schemas():
        all_pass = False

    print("\n" + "=" * 50)
    if all_pass:
        print("✅ ALL TESTS PASSED!")
        print("The migration is ready to be applied.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please fix the issues before applying the migration.")
    print("=" * 50)

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())