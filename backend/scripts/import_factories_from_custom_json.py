#!/usr/bin/env python3
"""
Import Factories from Custom JSON Format
=========================================
Converts and imports factory JSON files with nested structure.

Usage:
    python scripts/import_factories_from_custom_json.py --dir /tmp/import_factories
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

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
    # Remove leading tabs/whitespace
    s = s.lstrip('\t ')
    return s if s else None


def parse_datetime(value):
    """Parse datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace(' 00:00:00', ''))
    except:
        return None


def import_factory_from_custom_json(db, json_file: Path, dry_run: bool = False):
    """Import a single factory from custom JSON format."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate JSON structure - must have client_company
        if 'client_company' not in data:
            print(f"  ⚠️  SKIP: Invalid structure (missing client_company) - {json_file.name}")
            return 'skipped'

        # Extract nested data
        client = data.get('client_company', {})

        # Validate client_company has name
        if isinstance(client, dict):
            company_name = client.get('name')
        elif isinstance(client, str):
            company_name = client
            client = {'name': client}
        else:
            company_name = None

        if not company_name:
            print(f"  ⚠️  SKIP: Missing company name - {json_file.name}")
            return 'skipped'

        plant = data.get('plant', {})
        schedule = data.get('schedule', {})
        payment = data.get('payment', {})
        dispatch = data.get('dispatch_company', {})

        # Map to Factory model fields
        factory_data = {
            # Factory ID (use from JSON or generate from company + plant)
            'factory_id': clean_string(data.get('factory_id')),

            # Company info (client_company)
            'company_name': clean_string(client.get('name')),
            'company_address': clean_string(client.get('address')),
            'company_phone': clean_string(client.get('phone')),

            # Plant info
            'plant_name': clean_string(plant.get('name')) or '本社',  # Default to '本社' if not specified
            'plant_address': clean_string(plant.get('address')),
            'plant_phone': clean_string(plant.get('phone')),

            # Client responsible person
            'client_responsible_department': clean_string(client.get('responsible_person', {}).get('department')),
            'client_responsible_name': clean_string(client.get('responsible_person', {}).get('name')),
            'client_responsible_phone': clean_string(client.get('responsible_person', {}).get('phone')),

            # Client complaint handler
            'client_complaint_department': clean_string(client.get('complaint_handler', {}).get('department')),
            'client_complaint_name': clean_string(client.get('complaint_handler', {}).get('name')),
            'client_complaint_phone': clean_string(client.get('complaint_handler', {}).get('phone')),

            # Dispatch company (UNS Kikaku)
            'dispatch_responsible_department': clean_string(dispatch.get('responsible_person', {}).get('department')),
            'dispatch_responsible_name': clean_string(dispatch.get('responsible_person', {}).get('name')),
            'dispatch_responsible_phone': clean_string(dispatch.get('responsible_person', {}).get('phone')),

            'dispatch_complaint_department': clean_string(dispatch.get('complaint_handler', {}).get('department')),
            'dispatch_complaint_name': clean_string(dispatch.get('complaint_handler', {}).get('name')),
            'dispatch_complaint_phone': clean_string(dispatch.get('complaint_handler', {}).get('phone')),

            # Schedule info
            'work_hours_description': clean_string(schedule.get('work_hours')),
            'break_time_description': clean_string(schedule.get('break_time')),
            'calendar_description': clean_string(schedule.get('calendar')),
            'overtime_description': clean_string(schedule.get('overtime_labor')),
            'holiday_work_description': clean_string(schedule.get('non_work_day_labor')),

            # Conflict date
            'conflict_date': parse_datetime(schedule.get('conflict_date')),

            # Time unit
            'time_unit_minutes': int(float(schedule.get('time_unit') or 15)),

            # Payment info
            'closing_date': clean_string(payment.get('closing_date')),
            'payment_date': clean_string(payment.get('payment_date')),
            'bank_account': clean_string(payment.get('bank_account')),
            'worker_closing_date': clean_string(payment.get('worker_closing_date')),
            'worker_payment_date': clean_string(payment.get('worker_payment_date')),
            'worker_calendar': clean_string(payment.get('worker_calendar')),

            # Agreement
            'agreement_period': parse_datetime(data.get('agreement', {}).get('period')),
            'agreement_explainer': clean_string(data.get('agreement', {}).get('explainer')),

            'is_active': True,
        }

        # Check if factory already exists
        existing = db.query(Factory).filter(
            Factory.company_name == factory_data['company_name'],
            Factory.plant_name == factory_data['plant_name']
        ).first()

        if existing:
            print(f"  ⚠️  EXISTS: {factory_data['company_name']} - {factory_data['plant_name']}")
            factory = existing
            if not dry_run:
                # Update existing
                for key, value in factory_data.items():
                    if value is not None:
                        setattr(factory, key, value)
            result = 'updated'
        else:
            if not dry_run:
                factory = Factory(**factory_data)
                db.add(factory)
                db.flush()
            else:
                factory = type('Factory', (), {'id': 0})()
            print(f"  ✅ CREATED: {factory_data['company_name']} - {factory_data['plant_name']}")
            result = 'created'

        # Import lines
        # Handle two formats:
        # 1. lines: [{assignment, job}, ...] (multiple lines)
        # 2. assignment + job at root level (single line)
        lines_data = data.get('lines', [])

        # If no 'lines' array but has 'assignment' at root, treat as single line
        if not lines_data and 'assignment' in data:
            lines_data = [{'assignment': data.get('assignment'), 'job': data.get('job')}]

        lines_created = 0
        lines_updated = 0

        for line_data in lines_data:
            assignment = line_data.get('assignment', {})
            job = line_data.get('job', {})

            # Build supervisor info string if available
            supervisor = assignment.get('supervisor', {})
            supervisor_info = None
            if supervisor:
                parts = []
                if supervisor.get('department'):
                    parts.append(clean_string(supervisor.get('department')))
                if supervisor.get('name'):
                    parts.append(clean_string(supervisor.get('name')))
                if supervisor.get('phone'):
                    parts.append(clean_string(supervisor.get('phone')))
                if parts:
                    supervisor_info = ' / '.join(parts)

            line_info = {
                'factory_id': factory.id,
                'department': clean_string(assignment.get('department')),
                'line_name': clean_string(assignment.get('line')),
                'job_description': clean_string(job.get('description')),
                'supervisor_department': clean_string(supervisor.get('department')) if supervisor else None,
                'supervisor_name': clean_string(supervisor.get('name')) if supervisor else None,
                'supervisor_phone': clean_string(supervisor.get('phone')) if supervisor else None,
                'supervisor_position': None,  # Not in JSON currently
                'hourly_rate': job.get('hourly_rate'),
                'is_active': True,
            }

            if not dry_run:
                existing_line = db.query(FactoryLine).filter(
                    FactoryLine.factory_id == factory.id,
                    FactoryLine.department == line_info['department'],
                    FactoryLine.line_name == line_info['line_name']
                ).first()

                if existing_line:
                    # Update
                    for key, value in line_info.items():
                        if value is not None and key != 'factory_id':
                            setattr(existing_line, key, value)
                    lines_updated += 1
                else:
                    line = FactoryLine(**line_info)
                    db.add(line)
                    lines_created += 1

        if lines_created > 0 or lines_updated > 0:
            print(f"    📝 Lines: {lines_created} created, {lines_updated} updated")

        return result

    except Exception as e:
        print(f"  ❌ ERROR in {json_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return 'error'


def import_factories(directory: str, dry_run: bool = False):
    """Import all factories from directory."""
    print(f"\n{'='*70}")
    print(f"Import Factories from Custom JSON")
    print(f"{'='*70}")
    print(f"Directory: {directory}")
    print(f"Mode: {'DRY RUN ⚠️' if dry_run else 'LIVE ✅'}")
    print(f"{'='*70}\n")

    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"❌ ERROR: Directory not found: {directory}")
        return False

    # Find JSON files
    json_files = list(dir_path.glob('*.json'))
    json_files = [f for f in json_files if 'mapping' not in f.name.lower() and 'index' not in f.name.lower()]

    total = len(json_files)
    print(f"Found {total} JSON files\n")

    if total == 0:
        print("No JSON files found.")
        return False

    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }

    db = SessionLocal()

    try:
        for idx, json_file in enumerate(json_files, 1):
            stats['total'] += 1
            print(f"[{idx}/{total}] {json_file.name}")

            result = import_factory_from_custom_json(db, json_file, dry_run)

            if result == 'created':
                stats['created'] += 1
            elif result == 'updated':
                stats['updated'] += 1
            elif result == 'skipped':
                stats['skipped'] += 1
            elif result == 'error':
                stats['errors'] += 1

        if not dry_run:
            db.commit()
            print("\n✅ Changes committed to database.")
        else:
            print("\n⚠️  DRY RUN - No changes made.")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"Total processed: {stats['total']}")
    print(f"Created:         {stats['created']}")
    print(f"Updated:         {stats['updated']}")
    print(f"Skipped:         {stats['skipped']}")
    print(f"Errors:          {stats['errors']}")
    print(f"{'='*70}\n")

    return stats['errors'] == 0


def main():
    parser = argparse.ArgumentParser(description="Import factories from custom JSON format")
    parser.add_argument("--dir", type=str, required=True, help="Directory with JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to database")
    args = parser.parse_args()

    success = import_factories(directory=args.dir, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
