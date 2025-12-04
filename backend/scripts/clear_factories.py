#!/usr/bin/env python3
"""
Clear Factories Database
========================
Elimina todas las fábricas y líneas de la base de datos.

ADVERTENCIA: Esta operación NO SE PUEDE DESHACER.

Usage:
    python scripts/clear_factories.py
    python scripts/clear_factories.py --confirm
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.factory import Factory, FactoryLine


def clear_factories(force: bool = False):
    """Clear all factories and lines from database."""

    db = SessionLocal()

    try:
        # Count current data
        factories_count = db.query(func.count(Factory.id)).scalar()
        lines_count = db.query(func.count(FactoryLine.id)).scalar()

        print("\n" + "="*70)
        print("CLEAR FACTORIES DATABASE")
        print("="*70)
        print(f"\n📊 DATOS ACTUALES:")
        print(f"   Fábricas: {factories_count}")
        print(f"   Líneas:   {lines_count}")
        print()

        if factories_count == 0 and lines_count == 0:
            print("✅ La base de datos ya está vacía.")
            return True

        # Confirmation
        if not force:
            print("⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos de fábricas.")
            print("   Esta acción NO SE PUEDE DESHACER.\n")

            response = input("¿Estás seguro? Escribe 'SI' para confirmar: ").strip()

            if response != "SI":
                print("\n❌ Operación cancelada.")
                return False

        print("\n🗑️  Eliminando datos...")

        # First, unlink employees from factories and lines
        from app.models.employee import Employee

        employees_updated = db.query(Employee).filter(
            (Employee.factory_id.isnot(None)) | (Employee.factory_line_id.isnot(None))
        ).update({
            'factory_id': None,
            'factory_line_id': None,
            'company_name': None,
            'plant_name': None,
            'department': None,
            'line_name': None
        }, synchronize_session=False)

        if employees_updated > 0:
            print(f"   ✅ {employees_updated} empleados desvinculados de fábricas")

        # Delete all lines (now safe)
        deleted_lines = db.query(FactoryLine).delete()
        print(f"   ✅ {deleted_lines} líneas eliminadas")

        # Delete all factories
        deleted_factories = db.query(Factory).delete()
        print(f"   ✅ {deleted_factories} fábricas eliminadas")

        # Commit changes
        db.commit()

        print("\n" + "="*70)
        print("✅ BASE DE DATOS LIMPIADA EXITOSAMENTE")
        print("="*70)
        print("\nAhora puedes importar tus JSON desde cero.\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Clear all factories from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode (asks for confirmation)
    python scripts/clear_factories.py

    # Force mode (no confirmation)
    python scripts/clear_factories.py --confirm
        """
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    success = clear_factories(force=args.confirm)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
