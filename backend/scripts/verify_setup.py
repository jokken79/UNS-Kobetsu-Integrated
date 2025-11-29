#!/usr/bin/env python3
"""
Verify Setup Script

Verifica que el setup del backend está correcto antes de ejecutar.
Ejecutar con: docker exec uns-kobetsu-backend python scripts/verify_setup.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify_imports():
    """Verifica que todos los imports críticos funcionan."""
    errors = []

    # Security imports
    try:
        from app.core.security import get_current_user, require_role, get_password_hash
        print("✅ Security imports OK (get_current_user, require_role, get_password_hash)")
    except ImportError as e:
        errors.append(f"❌ Security import error: {e}")

    # API helpers
    try:
        from app.api.v1.helpers import (
            get_contract_or_404,
            get_employee_or_404,
            get_factory_or_404,
            validate_contract_status,
            validate_date_range
        )
        print("✅ API helpers imports OK")
    except ImportError as e:
        errors.append(f"❌ API helpers import error: {e}")

    # Services
    try:
        from app.services.kobetsu_service import KobetsuService
        print("✅ KobetsuService import OK")
    except ImportError as e:
        errors.append(f"❌ KobetsuService import error: {e}")

    try:
        from app.services.kobetsu_pdf_service import KobetsuPDFService
        print("✅ KobetsuPDFService import OK")
    except ImportError as e:
        errors.append(f"❌ KobetsuPDFService import error: {e}")

    try:
        from app.services.contract_logic_service import ContractLogicService
        print("✅ ContractLogicService import OK")
    except ImportError as e:
        errors.append(f"❌ ContractLogicService import error: {e}")

    # Models
    try:
        from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
        from app.models.employee import Employee
        from app.models.factory import Factory, FactoryLine
        from app.models.company import Company
        from app.models.plant import Plant
        print("✅ All models import OK")
    except ImportError as e:
        errors.append(f"❌ Models import error: {e}")

    # Schemas
    try:
        from app.schemas.kobetsu_keiyakusho import (
            KobetsuKeiyakushoCreate,
            KobetsuKeiyakushoUpdate,
            KobetsuKeiyakushoResponse
        )
        print("✅ Schemas import OK")
    except ImportError as e:
        errors.append(f"❌ Schemas import error: {e}")

    return errors


def verify_config():
    """Verifica la configuración."""
    errors = []

    try:
        from app.core.config import settings

        # Check JWT SECRET_KEY
        if "change-in-production" in settings.JWT_SECRET_KEY.lower() or \
           "insecure" in settings.JWT_SECRET_KEY.lower() or \
           "dev" in settings.JWT_SECRET_KEY.lower():
            errors.append("⚠️  WARNING: JWT SECRET_KEY appears to be a development/insecure key")
        else:
            print("✅ JWT SECRET_KEY configured (production-ready)")

        # Check DATABASE_URL
        db_url = settings.get_database_url()
        if db_url:
            print(f"✅ DATABASE_URL configured: {db_url[:30]}...")
        else:
            errors.append("❌ DATABASE_URL not configured")

        # Check REDIS_URL
        redis_url = settings.REDIS_URL
        if redis_url:
            print(f"✅ REDIS_URL configured: {redis_url[:30]}...")
        else:
            errors.append("❌ REDIS_URL not configured")

        # Check CORS origins
        if settings.CORS_ORIGINS:
            print(f"✅ CORS_ORIGINS configured: {len(settings.CORS_ORIGINS)} origins")
        else:
            errors.append("⚠️  WARNING: CORS_ORIGINS is empty")

    except Exception as e:
        errors.append(f"❌ Config error: {e}")

    return errors


def verify_database_connection():
    """Verifica la conexión a la base de datos."""
    errors = []

    try:
        from app.core.database import SessionLocal, engine

        # Try to connect
        with engine.connect() as conn:
            print("✅ Database connection successful")

        # Try to create a session
        db = SessionLocal()
        try:
            # Execute a simple query
            from sqlalchemy import text
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database session and query execution OK")
        finally:
            db.close()

    except Exception as e:
        errors.append(f"❌ Database connection error: {e}")

    return errors


def verify_alembic_migrations():
    """Verifica el estado de las migraciones."""
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from app.core.database import engine

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)

        # Get current revision from database
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        # Get head revision from migration scripts
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            print(f"✅ Database migrations up to date (revision: {current_rev})")
            return []
        else:
            return [f"⚠️  WARNING: Database not up to date. Current: {current_rev}, Head: {head_rev}"]

    except Exception as e:
        return [f"⚠️  WARNING: Could not verify migrations: {e}"]


def main():
    """Función principal."""
    print("\n" + "="*60)
    print("UNS Kobetsu - Setup Verification")
    print("="*60 + "\n")

    all_errors = []

    # 1. Verify imports
    print("🔍 Checking imports...")
    errors = verify_imports()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  {e}")
    print()

    # 2. Verify configuration
    print("🔍 Checking configuration...")
    errors = verify_config()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  {e}")
    print()

    # 3. Verify database connection
    print("🔍 Checking database connection...")
    errors = verify_database_connection()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  {e}")
    print()

    # 4. Verify migrations
    print("🔍 Checking migrations...")
    errors = verify_alembic_migrations()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  {e}")
    print()

    # Summary
    print("="*60)
    if all_errors:
        error_count = len([e for e in all_errors if e.startswith("❌")])
        warning_count = len([e for e in all_errors if e.startswith("⚠️")])

        if error_count > 0:
            print(f"❌ VERIFICATION FAILED: {error_count} error(s), {warning_count} warning(s)")
            print("\nErrors found:")
            for e in all_errors:
                if e.startswith("❌"):
                    print(f"  {e}")
            if warning_count > 0:
                print("\nWarnings:")
                for e in all_errors:
                    if e.startswith("⚠️"):
                        print(f"  {e}")
            return 1
        else:
            print(f"⚠️  VERIFICATION PASSED with {warning_count} warning(s)")
            for e in all_errors:
                print(f"  {e}")
            return 0
    else:
        print("✅ ALL VERIFICATIONS PASSED!")
        print("\nYour backend setup is ready to use.")
        return 0


if __name__ == "__main__":
    exit_code = main()
    print("\n" + "="*60 + "\n")
    sys.exit(exit_code)
