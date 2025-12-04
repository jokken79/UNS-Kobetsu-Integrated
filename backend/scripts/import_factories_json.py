#!/usr/bin/env python3
"""
Import Factories from JSON files

Imports factory data from config/factories/*.json files.

Usage:
    python scripts/import_factories_json.py --dir /app/factories
    python scripts/import_factories_json.py --dir /app/factories --dry-run
"""
import argparse
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.factory import Factory, FactoryLine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(value) -> date | None:
    """Parse date from string."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        # Format: "2025-09-30 00:00:00" or "2025-09-30"
        dt = datetime.strptime(str(value).split()[0], "%Y-%m-%d")
        return dt.date()
    except ValueError as e:
        logger.debug(f"Could not parse date value '{value}': {e}")
        return None


def calculate_break_minutes(break_time_str: str | None) -> int:
    """
    Calculate total break minutes from break time description.
    Mimics frontend's calculateBreakMinutes function.
    """
    if not break_time_str:
        return 60  # default

    # Try to extract time ranges like "10:30~10:40" or "10:30～10:40"
    # Also handle Japanese time format "11時00分～11時45分"
    total_minutes = 0

    # Normalize separators
    normalized = break_time_str.replace('～', '~').replace('時', ':').replace('分', '')

    # Find patterns like HH:MM~HH:MM
    pattern = r'(\d{1,2}):(\d{2})[~](\d{1,2}):(\d{2})'
    matches = re.findall(pattern, normalized)

    for start_h, start_m, end_h, end_m in matches:
        start = int(start_h) * 60 + int(start_m)
        end = int(end_h) * 60 + int(end_m)
        if end < start:
            end += 24 * 60  # overnight
        total_minutes += end - start

    # If no matches found, try to parse Japanese descriptive format
    if total_minutes == 0:
        # Look for numbers followed by "分" (minutes) like "45分"
        minute_pattern = r'(\d+)\s*分'
        minute_matches = re.findall(minute_pattern, break_time_str)
        for m in minute_matches:
            total_minutes += int(m)

    # Fallback to default 60 if still zero
    return total_minutes if total_minutes > 0 else 60


def parse_work_hours(work_hours_str: str | None) -> tuple:
    """
    Parse work hours string to extract day_shift_start, day_shift_end,
    night_shift_start, night_shift_end.
    Returns (day_start, day_end, night_start, night_end) as time objects or None.
    """
    if not work_hours_str:
        return (None, None, None, None)
    
    # Example: "昼勤：7時00分～15時30分　夜勤：19時00分～3時30分"
    # Use regex to extract times
    import re
    # Pattern for Japanese time format: 7時00分～15時30分
    pattern = r'(\d{1,2})時(\d{2})分[～~](\d{1,2})時(\d{2})分'
    matches = re.findall(pattern, work_hours_str)
    
    day_start = day_end = night_start = night_end = None
    if len(matches) >= 1:
        h1, m1, h2, m2 = matches[0]
        day_start = datetime.strptime(f"{h1}:{m1}", "%H:%M").time()
        day_end = datetime.strptime(f"{h2}:{m2}", "%H:%M").time()
    if len(matches) >= 2:
        h1, m1, h2, m2 = matches[1]
        night_start = datetime.strptime(f"{h1}:{m1}", "%H:%M").time()
        night_end = datetime.strptime(f"{h2}:{m2}", "%H:%M").time()
    
    return (day_start, day_end, night_start, night_end)


def parse_overtime_limits(overtime_str: str | None) -> dict:
    """
    Parse overtime description to extract limits.
    Returns dict with keys:
    - overtime_max_hours_day
    - overtime_max_hours_month
    - overtime_max_hours_year
    - overtime_special_max_month
    - overtime_special_count_year
    """
    if not overtime_str:
        return {}
    
    result = {}
    # Example: "3時間/日、42時間/月、320時間/年迄とする。但し、特別条項の申請により、80時間/月、720時間/年迄延長できる。申請は6回/年迄とする。"
    # Extract numbers followed by "時間/日", "時間/月", "時間/年"
    import re
    day_match = re.search(r'(\d+(?:\.\d+)?)\s*時間/日', overtime_str)
    month_match = re.search(r'(\d+(?:\.\d+)?)\s*時間/月', overtime_str)
    year_match = re.search(r'(\d+(?:\.\d+)?)\s*時間/年', overtime_str)
    special_month_match = re.search(r'特別条項.*?(\d+(?:\.\d+)?)\s*時間/月', overtime_str)
    special_year_match = re.search(r'特別条項.*?(\d+(?:\.\d+)?)\s*時間/年', overtime_str)
    special_count_match = re.search(r'申請は\s*(\d+)\s*回/年', overtime_str)
    
    if day_match:
        result['overtime_max_hours_day'] = Decimal(day_match.group(1))
    if month_match:
        result['overtime_max_hours_month'] = Decimal(month_match.group(1))
    if year_match:
        result['overtime_max_hours_year'] = int(year_match.group(1))
    if special_month_match:
        result['overtime_special_max_month'] = Decimal(special_month_match.group(1))
    if special_year_match:
        result['overtime_special_count_year'] = int(special_year_match.group(1))
    if special_count_match:
        result['overtime_special_count_year'] = int(special_count_match.group(1))
    
    return result


def parse_holiday_work_max_days(holiday_str: str | None) -> int | None:
    """
    Parse holiday work description to extract max days per month.
    Returns integer or None.
    """
    if not holiday_str:
        return None
    # Example: "１ヶ月に２日の範囲内で命ずることができる。"
    import re
    match = re.search(r'(\d+)\s*日の範囲', holiday_str)
    if match:
        return int(match.group(1))
    return None


def extract_position_from_name(full_name: str | None) -> tuple[str | None, str | None]:
    """
    Extract position and name from Japanese full name.
    Example: "主任　山口　アデルソン" -> position="主任", name="山口　アデルソン"
    """
    if not full_name:
        return (None, None)
    # Split by spaces or Japanese spaces
    parts = full_name.split()
    if len(parts) >= 2 and len(parts[0]) <= 4:  # Assume first part is position
        position = parts[0]
        name = ' '.join(parts[1:])
        return (position, name)
    return (None, full_name)


def json_to_factory(data: dict) -> dict:
    """Convert JSON structure to Factory model fields."""
    client = data.get('client_company', {})
    plant = data.get('plant', {})
    dispatch = data.get('dispatch_company', {})
    schedule = data.get('schedule', {})
    payment = data.get('payment', {})
    agreement = data.get('agreement', {})

    break_time_description = schedule.get('break_time')
    break_minutes = calculate_break_minutes(break_time_description)

    # Parse work hours for shift times
    work_hours_str = schedule.get('work_hours')
    day_shift_start, day_shift_end, night_shift_start, night_shift_end = parse_work_hours(work_hours_str)

    # Parse overtime limits
    overtime_str = schedule.get('overtime_labor')
    overtime_limits = parse_overtime_limits(overtime_str)

    # Parse holiday work max days
    holiday_str = schedule.get('non_work_day_labor')
    holiday_work_max_days_month = parse_holiday_work_max_days(holiday_str)

    # Extract positions from names
    client_resp_name = client.get('responsible_person', {}).get('name')
    client_resp_position, client_resp_name_clean = extract_position_from_name(client_resp_name)
    client_comp_name = client.get('complaint_handler', {}).get('name')
    client_comp_position, client_comp_name_clean = extract_position_from_name(client_comp_name)

    # Build factory dict
    factory_dict = {
        'factory_id': data.get('factory_id'),
        'company_name': client.get('name') or data.get('client_company'),
        'company_address': client.get('address'),
        'company_phone': client.get('phone'),
        'company_fax': client.get('fax'),  # New field
        'client_responsible_department': client.get('responsible_person', {}).get('department'),
        'client_responsible_position': client_resp_position,
        'client_responsible_name': client_resp_name_clean,
        'client_responsible_phone': client.get('responsible_person', {}).get('phone'),
        'client_complaint_department': client.get('complaint_handler', {}).get('department'),
        'client_complaint_position': client_comp_position,
        'client_complaint_name': client_comp_name_clean,
        'client_complaint_phone': client.get('complaint_handler', {}).get('phone'),
        'plant_name': plant.get('name') or data.get('plant_name', ''),
        'plant_address': plant.get('address'),
        'plant_phone': plant.get('phone'),
        'dispatch_responsible_department': dispatch.get('responsible_person', {}).get('department'),
        'dispatch_responsible_name': dispatch.get('responsible_person', {}).get('name'),
        'dispatch_responsible_phone': dispatch.get('responsible_person', {}).get('phone'),
        'dispatch_complaint_department': dispatch.get('complaint_handler', {}).get('department'),
        'dispatch_complaint_name': dispatch.get('complaint_handler', {}).get('name'),
        'dispatch_complaint_phone': dispatch.get('complaint_handler', {}).get('phone'),
        'work_hours_description': work_hours_str,
        'day_shift_start': day_shift_start,
        'day_shift_end': day_shift_end,
        'night_shift_start': night_shift_start,
        'night_shift_end': night_shift_end,
        'break_time_description': break_time_description,
        'calendar_description': schedule.get('calendar'),
        'overtime_description': overtime_str,
        'overtime_max_hours_day': overtime_limits.get('overtime_max_hours_day'),
        'overtime_max_hours_month': overtime_limits.get('overtime_max_hours_month'),
        'overtime_max_hours_year': overtime_limits.get('overtime_max_hours_year'),
        'overtime_special_max_month': overtime_limits.get('overtime_special_max_month'),
        'overtime_special_count_year': overtime_limits.get('overtime_special_count_year'),
        'holiday_work_description': holiday_str,
        'holiday_work_max_days_month': holiday_work_max_days_month,
        'conflict_date': parse_date(schedule.get('conflict_date')),
        'contract_start_date': parse_date(schedule.get('start_date')),
        'contract_end_date': parse_date(schedule.get('end_date')),
        'break_minutes': break_minutes,
        'time_unit_minutes': Decimal(schedule.get('time_unit', '15') or '15'),
        'closing_date': payment.get('closing_date'),
        'payment_date': payment.get('payment_date'),
        'bank_account': payment.get('bank_account'),
        'worker_closing_date': payment.get('worker_closing_date'),
        'worker_payment_date': payment.get('worker_payment_date'),
        'worker_calendar': payment.get('worker_calendar'),
        'agreement_period': parse_date(agreement.get('period')),
        'agreement_explainer': agreement.get('explainer'),
        'is_active': True,
    }
    return factory_dict


def json_to_lines(data: dict, factory_db_id: int) -> list[dict]:
    """Convert JSON lines to FactoryLine model fields."""
    lines_data = data.get('lines', [])
    result = []

    for i, line in enumerate(lines_data):
        assignment = line.get('assignment', {})
        job = line.get('job', {})
        supervisor = assignment.get('supervisor', {})

        # Extract supervisor position from name
        supervisor_name = supervisor.get('name')
        supervisor_position, supervisor_name_clean = extract_position_from_name(supervisor_name)

        line_dict = {
            'factory_id': factory_db_id,
            'line_id': line.get('line_id'),
            'department': assignment.get('department'),
            'line_name': assignment.get('line'),
            'supervisor_department': supervisor.get('department'),
            'supervisor_position': supervisor_position,
            'supervisor_name': supervisor_name_clean,
            'supervisor_phone': supervisor.get('phone'),
            'job_description': job.get('description'),
            'job_description_detail': job.get('description2'),
            'hourly_rate': Decimal(str(job.get('hourly_rate', 0) or 0)),
            'is_active': True,
            'display_order': i,
        }
        result.append(line_dict)

    return result


def import_factories(json_dir: str, dry_run: bool = False):
    """Import factories from JSON files."""
    print(f"\n{'='*60}")
    print(f"Importing factories from: {json_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"ERROR: Directory not found: {json_dir}")
        return False

    # Find all JSON files (exclude backup, mapping files)
    json_files = [f for f in json_path.glob("*.json")
                  if not f.name.startswith('factory_id')
                  and '_mapping' not in f.name]

    print(f"Found {len(json_files)} JSON files\n")

    stats = {
        'files': 0,
        'factories_created': 0,
        'factories_updated': 0,
        'lines_created': 0,
        'lines_updated': 0,
        'errors': 0,
    }

    db = SessionLocal()

    try:
        for json_file in sorted(json_files):
            stats['files'] += 1

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                factory_id = data.get('factory_id')
                if not factory_id:
                    print(f"  SKIP {json_file.name}: No factory_id")
                    continue

                factory_data = json_to_factory(data)

                # Check if factory exists
                existing = db.query(Factory).filter(
                    Factory.factory_id == factory_id
                ).first()

                if existing:
                    # Update existing factory
                    if not dry_run:
                        for key, value in factory_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                    stats['factories_updated'] += 1
                    factory_db_id = existing.id
                    action = "UPDATE"
                else:
                    # Create new factory
                    if not dry_run:
                        factory = Factory(**factory_data)
                        db.add(factory)
                        db.flush()
                        factory_db_id = factory.id
                    else:
                        factory_db_id = -1
                    stats['factories_created'] += 1
                    action = "CREATE"

                # Process lines
                lines_data = json_to_lines(data, factory_db_id)
                for line_data in lines_data:
                    if dry_run:
                        stats['lines_created'] += 1
                        continue

                    # Check if line exists
                    existing_line = db.query(FactoryLine).filter(
                        FactoryLine.factory_id == factory_db_id,
                        FactoryLine.line_id == line_data.get('line_id')
                    ).first()

                    if existing_line:
                        for key, value in line_data.items():
                            if value is not None and key != 'factory_id':
                                setattr(existing_line, key, value)
                        stats['lines_updated'] += 1
                    else:
                        line = FactoryLine(**line_data)
                        db.add(line)
                        stats['lines_created'] += 1

                print(f"  {action}: {factory_id} ({len(lines_data)} lines)")

            except json.JSONDecodeError as e:
                stats['errors'] += 1
                logger.error(f"  ERROR {json_file.name}: Invalid JSON - {e}", exc_info=True)
                print(f"  ERROR {json_file.name}: Invalid JSON - {e}")
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"  ERROR {json_file.name}: {e}", exc_info=True)
                print(f"  ERROR {json_file.name}: {e}")

        if not dry_run:
            db.commit()
            print("\nChanges committed to database.")
        else:
            print("\nDRY RUN - No changes made.")

    except Exception as e:
        logger.critical(f"FATAL ERROR: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    print(f"\n{'='*60}")
    print("IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed:     {stats['files']}")
    print(f"Factories created:   {stats['factories_created']}")
    print(f"Factories updated:   {stats['factories_updated']}")
    print(f"Lines created:       {stats['lines_created']}")
    print(f"Lines updated:       {stats['lines_updated']}")
    print(f"Errors:              {stats['errors']}")
    print(f"{'='*60}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Import factories from JSON files"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="/app/factories",
        help="Directory containing factory JSON files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually save to database"
    )

    args = parser.parse_args()
    success = import_factories(args.dir, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
