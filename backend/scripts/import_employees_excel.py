#!/usr/bin/env python3
"""
Import Employees from Excel - DBGenzaiX Sheet

Imports employee data from the hidden DBGenzaiX sheet in the
社員台帳 (Employee Registry) Excel file.

Usage:
    python scripts/import_employees_excel.py --file /app/employees.xlsm
    python scripts/import_employees_excel.py --file /app/employees.xlsm --dry-run
"""
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.employee import Employee

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Column mapping: Excel column index (1-based) -> Employee model field
COLUMN_MAPPING = {
    1: 'status_raw',           # 現在 (退社 = resigned, else active)
    2: 'employee_number',      # 社員№
    4: 'company_name',         # 派遣先
    5: 'department',           # 配属先
    6: 'line_name',            # 配属ライン
    7: 'position',             # 仕事内容
    8: 'full_name_kanji',      # 氏名
    9: 'full_name_kana',       # カナ
    10: 'gender',              # 性別
    11: 'nationality',         # 国籍
    12: 'date_of_birth',       # 生年月日
    14: 'hourly_rate',         # 時給
    16: 'billing_rate',        # 請求単価
    23: 'visa_expiry_date',    # ビザ期限
    25: 'visa_type',           # ビザ種類
    26: 'postal_code',         # 〒
    27: 'address',             # 住所
    28: 'apartment_name',      # アパート
    30: 'hire_date',           # 入社日
    31: 'termination_date',    # 退社日
    33: 'insurance_status',    # 社保加入
    35: 'notes',               # 備考
    37: 'drivers_license',     # 免許種類
    38: 'drivers_license_expiry',  # 免許期限
    41: 'qualifications',      # 日本語検定
}


def parse_date(value) -> date | None:
    """Parse date from Excel cell value."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value or value in ('0', '00:00:00'):
            return None
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    if isinstance(value, (int, float)):
        # Excel serial date
        try:
            from datetime import timedelta
            excel_epoch = datetime(1899, 12, 30)
            return (excel_epoch + timedelta(days=int(value))).date()
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse Excel serial date '{value}': {e}")
    return None


def parse_decimal(value) -> Decimal | None:
    """Parse decimal from Excel cell value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        value = value.strip().replace(',', '')
        if not value or value == '0':
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            return None
    return None


def parse_status(value) -> str:
    """Convert Japanese status to enum value."""
    if value is None:
        return 'active'
    status_str = str(value).strip().lower()
    if '退社' in status_str or 'resigned' in status_str:
        return 'resigned'
    if '休職' in status_str:
        return 'on_leave'
    if '転籍' in status_str:
        return 'transferred'
    return 'active'


def parse_gender(value) -> str | None:
    """Convert Japanese gender to model value."""
    if value is None:
        return None
    gender_str = str(value).strip()
    if gender_str in ('男', 'M', 'male'):
        return 'male'
    if gender_str in ('女', 'F', 'female'):
        return 'female'
    return 'other'


def clean_string(value) -> str | None:
    """Clean string value from Excel."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == 0:
            return None
        return str(value)
    s = str(value).strip()
    if s in ('0', ''):
        return None
    return s


def row_to_employee_dict(ws, row_num: int) -> dict:
    """Convert Excel row to employee dictionary."""
    data = {}

    for col_idx, field_name in COLUMN_MAPPING.items():
        cell_value = ws.cell(row=row_num, column=col_idx).value
        data[field_name] = cell_value

    # Process raw values into proper types
    employee_data = {
        'employee_number': clean_string(data.get('employee_number')),
        'full_name_kanji': clean_string(data.get('full_name_kanji')) or 'Unknown',
        'full_name_kana': clean_string(data.get('full_name_kana')) or 'Unknown',
        'gender': parse_gender(data.get('gender')),
        'nationality': clean_string(data.get('nationality')) or 'ベトナム',
        'date_of_birth': parse_date(data.get('date_of_birth')),
        'company_name': clean_string(data.get('company_name')),
        'department': clean_string(data.get('department')),
        'line_name': clean_string(data.get('line_name')),
        'position': clean_string(data.get('position')),
        'hourly_rate': parse_decimal(data.get('hourly_rate')),
        'billing_rate': parse_decimal(data.get('billing_rate')),
        'visa_type': clean_string(data.get('visa_type')),
        'visa_expiry_date': parse_date(data.get('visa_expiry_date')),
        'postal_code': clean_string(data.get('postal_code')),
        'address': clean_string(data.get('address')),
        'apartment_name': clean_string(data.get('apartment_name')),
        'hire_date': parse_date(data.get('hire_date')) or date.today(),
        'termination_date': parse_date(data.get('termination_date')),
        'status': parse_status(data.get('status_raw')),
        'notes': clean_string(data.get('notes')),
        'drivers_license': clean_string(data.get('drivers_license')),
        'drivers_license_expiry': parse_date(data.get('drivers_license_expiry')),
        'qualifications': clean_string(data.get('qualifications')),
    }

    # Set insurance flags based on 社保加入 status
    insurance_status = clean_string(data.get('insurance_status'))
    if insurance_status and insurance_status.upper() == 'OK':
        employee_data['has_health_insurance'] = True
        employee_data['has_pension_insurance'] = True
        employee_data['has_employment_insurance'] = True

    return employee_data


def import_employees(file_path: str, sheet_name: str = 'DBGenzaiX', dry_run: bool = False):
    """
    Import employees from Excel file using pandas (faster).

    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to import from
        dry_run: If True, don't actually save to database
    """
    print(f"\n{'='*60}")
    print(f"Importing employees from: {file_path}")
    print(f"Sheet: {sheet_name}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    # Load with pandas (faster than openpyxl for data reading)
    logger.info(f"Loading Excel file with pandas...")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        logger.error(f"ERROR loading file: {e}", exc_info=True)
        print(f"ERROR loading file: {e}")
        return False

    total_rows = len(df)
    print(f"Found {total_rows} rows\n")

    # Column name mapping (pandas uses 0-based from header row)
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

    # Stats
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

            try:
                # Extract employee data
                emp_number = clean_string(row.get('社員№'))
                if not emp_number:
                    stats['skipped'] += 1
                    continue

                employee_data = {
                    'employee_number': emp_number,
                    'full_name_kanji': clean_string(row.get('氏名')) or 'Unknown',
                    'full_name_kana': clean_string(row.get('カナ')) or 'Unknown',
                    'gender': parse_gender(row.get('性別')),
                    'nationality': clean_string(row.get('国籍')) or 'ベトナム',
                    'date_of_birth': parse_date(row.get('生年月日')),
                    'company_name': clean_string(row.get('派遣先')),
                    'department': clean_string(row.get('配属先')),
                    'line_name': clean_string(row.get('配属ライン')),
                    'position': clean_string(row.get('仕事内容')),
                    'hourly_rate': parse_decimal(row.get('時給')),
                    'billing_rate': parse_decimal(row.get('請求単価')),
                    'visa_type': clean_string(row.get('ビザ種類')),
                    'visa_expiry_date': parse_date(row.get('ビザ期限')),
                    'postal_code': clean_string(row.get('〒')),
                    'address': clean_string(row.get('住所')),
                    'apartment_name': clean_string(row.get('ｱﾊﾟｰﾄ', row.get('アパート'))),
                    'hire_date': parse_date(row.get('入社日')) or date.today(),
                    'termination_date': parse_date(row.get('退社日')),
                    'status': parse_status(row.get('現在')),
                    'notes': clean_string(row.get('備考')),
                    'drivers_license': clean_string(row.get('免許種類')),
                    'drivers_license_expiry': parse_date(row.get('免許期限')),
                    'qualifications': clean_string(row.get('日本語検定')),
                }

                # Insurance status
                insurance = clean_string(row.get('社保加入'))
                if insurance and insurance.upper() == 'OK':
                    employee_data['has_health_insurance'] = True
                    employee_data['has_pension_insurance'] = True
                    employee_data['has_employment_insurance'] = True

                # Check if exists
                existing = db.query(Employee).filter(
                    Employee.employee_number == emp_number
                ).first()

                if existing:
                    if not dry_run:
                        for key, value in employee_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                    stats['updated'] += 1
                else:
                    if not dry_run:
                        employee = Employee(**employee_data)
                        db.add(employee)
                        # Flush to detect duplicates immediately
                        try:
                            db.flush()
                        except IntegrityError:
                            db.rollback()
                            stats['errors'] += 1
                            print(f"  DUPLICATE: {emp_number} - skipped")
                            continue
                    stats['created'] += 1

                # Commit every 100 rows to avoid memory issues
                if stats['total'] % 100 == 0:
                    if not dry_run:
                        db.commit()
                    print(f"  Processed {stats['total']}/{total_rows} rows...")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"  ERROR row {idx}: {e}", exc_info=True)
                print(f"  ERROR row {idx}: {e}")
                continue

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
    print(f"Total rows processed: {stats['total']}")
    print(f"Created:              {stats['created']}")
    print(f"Updated:              {stats['updated']}")
    print(f"Skipped:              {stats['skipped']}")
    print(f"Errors:               {stats['errors']}")
    print(f"{'='*60}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Import employees from Excel DBGenzaiX sheet"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="/app/employees.xlsm",
        help="Path to Excel file"
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default="DBGenzaiX",
        help="Sheet name to import from"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually save to database"
    )

    args = parser.parse_args()

    success = import_employees(
        file_path=args.file,
        sheet_name=args.sheet,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
