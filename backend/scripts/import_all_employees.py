#!/usr/bin/env python3
"""
Import ALL Employees from Excel - Including those without line assignment
=========================================================================
Imports ALL employee data from Excel, including employees without ライン.

Usage:
    python scripts/import_all_employees.py --file /tmp/employees.xlsm
    python scripts/import_all_employees.py --file /tmp/employees.xlsm --sheet DBGenzaiX --dry-run
"""
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.employee import Employee

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_string(value):
    """Clean string value."""
    if value is None or pd.isna(value):
        return None
    s = str(value).strip()
    return s if s and s not in ('nan', 'NaN', 'None', '0') else None


def parse_date(value):
    """Parse date from Excel cell value."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value or value in ('0', '00:00:00', 'nan', 'NaN'):
            return None
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def parse_decimal(value):
    """Parse decimal from Excel cell value."""
    if value is None or pd.isna(value):
        return None
    try:
        return Decimal(str(value))
    except:
        return None


def parse_gender(value):
    """Parse gender from Excel value."""
    if not value or pd.isna(value):
        return None
    s = str(value).strip().upper()
    if s in ('M', '男', '男性', 'MALE'):
        return 'M'
    elif s in ('F', '女', '女性', 'FEMALE'):
        return 'F'
    return None


def parse_status(value):
    """Parse employee status."""
    if not value or pd.isna(value):
        return 'active'
    s = str(value).strip()
    # If contains 退社 or 退職, mark as resigned
    if '退社' in s or '退職' in s:
        return 'resigned'
    return 'active'


def import_employees(file_path: str, sheet_name: str = 'DBGenzaiX', dry_run: bool = False):
    """
    Import ALL employees from Excel, including those without line assignment.
    """
    print(f"\n{'='*70}")
    print(f"Import ALL Employees from Excel")
    print(f"{'='*70}")
    print(f"File: {file_path}")
    print(f"Sheet: {sheet_name}")
    print(f"Mode: {'DRY RUN ⚠️' if dry_run else 'LIVE ✅'}")
    print(f"{'='*70}\n")

    # Load Excel file
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        logger.error(f"ERROR loading file: {e}")
        return False

    total_rows = len(df)
    print(f"Found {total_rows} rows in sheet '{sheet_name}'\n")

    # Column mapping - adjust based on your Excel structure
    col_map = {
        '現在': 'status_raw',
        '社員№': 'employee_number',
        '派遣先': 'company_name',
        '配属先': 'department',
        '配属ライン': 'line_name',
        '仕事内容': 'position',
        '氏名': 'full_name_kanji',
        'カナ': 'full_name_kana',
        '性別': 'gender',
        '国籍': 'nationality',
        '生年月日': 'date_of_birth',
        '時給': 'hourly_rate',
        '請求単価': 'billing_rate',
        'ビザ期限': 'visa_expiry_date',
        'ビザ種類': 'visa_type',
        '〒': 'postal_code',
        '住所': 'address',
        'アパート': 'apartment_name',
        'ｱﾊﾟｰﾄ': 'apartment_name',
        '入社日': 'hire_date',
        '退社日': 'termination_date',
        '社保加入': 'insurance_status',
        '備考': 'notes',
        '免許種類': 'drivers_license',
        '免許期限': 'drivers_license_expiry',
        '日本語検定': 'qualifications',
    }

    # Rename columns
    df = df.rename(columns=col_map)

    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }

    db = SessionLocal()

    try:
        for idx, row in df.iterrows():
            stats['total'] += 1

            # Skip if no employee number
            employee_number = clean_string(row.get('employee_number'))
            if not employee_number:
                logger.debug(f"[{idx+1}] Skipping row with no employee number")
                stats['skipped'] += 1
                continue

            # Skip if no name
            full_name = clean_string(row.get('full_name_kanji'))
            if not full_name:
                logger.debug(f"[{idx+1}] Skipping employee {employee_number} with no name")
                stats['skipped'] += 1
                continue

            # Build employee data - EVEN WITHOUT LINE INFO
            employee_data = {
                'employee_number': employee_number,
                'full_name_kanji': full_name,
                'full_name_kana': clean_string(row.get('full_name_kana')) or full_name,
                'gender': parse_gender(row.get('gender')),
                'nationality': clean_string(row.get('nationality')) or 'ベトナム',
                'date_of_birth': parse_date(row.get('date_of_birth')),
                'company_name': clean_string(row.get('company_name')),  # Can be null
                'department': clean_string(row.get('department')),      # Can be null
                'line_name': clean_string(row.get('line_name')),        # Can be null
                'position': clean_string(row.get('position')),
                'hourly_rate': parse_decimal(row.get('hourly_rate')),
                'billing_rate': parse_decimal(row.get('billing_rate')),
                'visa_type': clean_string(row.get('visa_type')),
                'visa_expiry_date': parse_date(row.get('visa_expiry_date')),
                'postal_code': clean_string(row.get('postal_code')),
                'address': clean_string(row.get('address')),
                'apartment_name': clean_string(row.get('apartment_name')),
                'hire_date': parse_date(row.get('hire_date')) or date.today(),
                'termination_date': parse_date(row.get('termination_date')),
                'status': parse_status(row.get('status_raw')),
                'notes': clean_string(row.get('notes')),
                'drivers_license': clean_string(row.get('drivers_license')),
                'drivers_license_expiry': parse_date(row.get('drivers_license_expiry')),
                'qualifications': clean_string(row.get('qualifications')),
            }

            # Set insurance flags
            insurance_status = clean_string(row.get('insurance_status'))
            if insurance_status and insurance_status.upper() == 'OK':
                employee_data['has_health_insurance'] = True
                employee_data['has_pension_insurance'] = True
                employee_data['has_employment_insurance'] = True

            if not dry_run:
                # Check if employee exists
                existing = db.query(Employee).filter(
                    Employee.employee_number == employee_number
                ).first()

                try:
                    if existing:
                        # Update existing employee
                        for key, value in employee_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                        logger.info(f"[{idx+1}/{total_rows}] ⚠️  UPDATED: {employee_number} - {full_name}")
                        stats['updated'] += 1
                    else:
                        # Create new employee
                        employee = Employee(**employee_data)
                        db.add(employee)
                        db.flush()
                        logger.info(f"[{idx+1}/{total_rows}] ✅ CREATED: {employee_number} - {full_name}")
                        stats['created'] += 1

                except Exception as e:
                    logger.error(f"[{idx+1}] ❌ ERROR: {employee_number} - {e}")
                    stats['errors'] += 1
                    continue
            else:
                logger.info(f"[{idx+1}/{total_rows}] {employee_number} - {full_name} (status: {employee_data['status']})")

        if not dry_run:
            db.commit()
            print(f"\n✅ Changes committed to database.")
        else:
            print(f"\n⚠️  DRY RUN - No changes made.")

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()

    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"Total rows processed: {stats['total']}")
    print(f"Created:              {stats['created']}")
    print(f"Updated:              {stats['updated']}")
    print(f"Skipped:              {stats['skipped']}")
    print(f"Errors:               {stats['errors']}")
    print(f"{'='*70}\n")

    return stats['errors'] == 0


def main():
    parser = argparse.ArgumentParser(description="Import ALL employees from Excel")
    parser.add_argument("--file", type=str, required=True, help="Path to Excel file")
    parser.add_argument("--sheet", type=str, default="DBGenzaiX", help="Sheet name (default: DBGenzaiX)")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to database")
    args = parser.parse_args()

    success = import_employees(
        file_path=args.file,
        sheet_name=args.sheet,
        dry_run=args.dry_run
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
