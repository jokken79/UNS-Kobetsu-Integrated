#!/usr/bin/env python3
"""
Import All Factories from Directory
====================================
Imports all factory JSON files from a directory at once.

Usage:
    python scripts/import_factories_directory.py --dir E:/config/factories
    python scripts/import_factories_directory.py --dir E:/config/factories --dry-run
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.factory import Factory, FactoryLine


def clean_string(value):
    """Clean string value."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def import_factory_from_json(db, json_file: Path, dry_run: bool = False):
    """Import a single factory from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract factory data
        factory_data = {
            'company_name': clean_string(data.get('company_name')),
            'plant_name': clean_string(data.get('plant_name')) or clean_string(data.get('factory_name')),
            'company_address': clean_string(data.get('company_address')),
            'company_phone': clean_string(data.get('company_phone')),
            'work_location': clean_string(data.get('work_location')),
            'work_content': clean_string(data.get('work_content')),
            'required_skills': clean_string(data.get('required_skills')),
            'safety_measures': clean_string(data.get('safety_measures')),
            'health_management': clean_string(data.get('health_management')),
            'work_days_per_week': data.get('work_days_per_week', 5),
            'work_start_time': clean_string(data.get('work_start_time', '08:00')),
            'work_end_time': clean_string(data.get('work_end_time', '17:00')),
            'break_time_minutes': data.get('break_time_minutes', 60),
            'overtime_hours_per_day': data.get('overtime_hours_per_day'),
            'overtime_hours_per_month': data.get('overtime_hours_per_month'),
            'holiday_work_days_per_month': data.get('holiday_work_days_per_month'),
            'contact_department': clean_string(data.get('contact_department')),
            'contact_person': clean_string(data.get('contact_person')),
            'contact_position': clean_string(data.get('contact_position')),
            'contact_phone': clean_string(data.get('contact_phone')),
        }

        # Check if factory already exists
        existing = db.query(Factory).filter(
            Factory.company_name == factory_data['company_name'],
            Factory.plant_name == factory_data['plant_name']
        ).first()

        if existing:
            print(f"  ⚠️  Factory exists: {factory_data['company_name']} - {factory_data['plant_name']}")
            factory = existing
            if not dry_run:
                # Update existing factory
                for key, value in factory_data.items():
                    if value is not None:
                        setattr(factory, key, value)
            result = 'updated'
        else:
            if not dry_run:
                factory = Factory(**factory_data)
                db.add(factory)
                db.flush()  # Get factory.id
            else:
                factory = type('Factory', (), {'id': 0})()
            print(f"  ✅ Created: {factory_data['company_name']} - {factory_data['plant_name']}")
            result = 'created'

        # Import factory lines
        lines_data = data.get('lines', [])
        lines_created = 0

        for line_data in lines_data:
            line_info = {
                'factory_id': factory.id,
                'department': clean_string(line_data.get('department')),
                'line_name': clean_string(line_data.get('line_name')),
                'work_content': clean_string(line_data.get('work_content')),
                'is_active': line_data.get('is_active', True),
            }

            if not dry_run:
                # Check if line exists
                existing_line = db.query(FactoryLine).filter(
                    FactoryLine.factory_id == factory.id,
                    FactoryLine.department == line_info['department'],
                    FactoryLine.line_name == line_info['line_name']
                ).first()

                if not existing_line:
                    line = FactoryLine(**line_info)
                    db.add(line)
                    lines_created += 1

        if lines_created > 0:
            print(f"    ➕ Added {lines_created} lines")

        return result

    except Exception as e:
        print(f"  ❌ ERROR in {json_file.name}: {e}")
        return 'error'


def import_factories_from_directory(directory: str, dry_run: bool = False):
    """Import all factories from JSON files in directory."""
    print(f"\n{'='*70}")
    print(f"Importing Factories from Directory")
    print(f"{'='*70}")
    print(f"Directory: {directory}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*70}\n")

    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"❌ ERROR: Directory does not exist: {directory}")
        return False

    # Find all JSON files
    json_files = list(dir_path.glob('*.json'))

    # Exclude mapping file
    json_files = [f for f in json_files if 'mapping' not in f.name.lower() and 'index' not in f.name.lower()]

    total_files = len(json_files)
    print(f"Found {total_files} factory JSON files\n")

    if total_files == 0:
        print("No JSON files found.")
        return False

    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'errors': 0,
    }

    db = SessionLocal()

    try:
        for json_file in json_files:
            stats['total'] += 1
            print(f"[{stats['total']}/{total_files}] Processing: {json_file.name}")

            result = import_factory_from_json(db, json_file, dry_run)

            if result == 'created':
                stats['created'] += 1
            elif result == 'updated':
                stats['updated'] += 1
            elif result == 'error':
                stats['errors'] += 1

        if not dry_run:
            db.commit()
            print("\n✅ Changes committed to database.")
        else:
            print("\n⚠️  DRY RUN - No changes made.")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"Total files processed: {stats['total']}")
    print(f"Created:               {stats['created']}")
    print(f"Updated:               {stats['updated']}")
    print(f"Errors:                {stats['errors']}")
    print(f"{'='*70}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Import all factories from JSON directory"
    )
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Directory containing factory JSON files (e.g., E:/config/factories)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually save to database"
    )

    args = parser.parse_args()

    success = import_factories_from_directory(
        directory=args.dir,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
