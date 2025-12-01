#!/usr/bin/env python3
"""
Crear Contratos para Empleados de 高雄工業 (Kaohsiung Kogyo)

Script automatizado para crear contratos individuales (個別契約書) para todos los
empleados que entraron desde marzo hasta septiembre 2025 en las fábricas de 高雄工業.

Período de contrato: Fecha de entrada del empleado hasta 2025-09-30

Usage:
    python scripts/create_employee_contracts_kaohsiung.py --dry-run  # Simular sin crear
    python scripts/create_employee_contracts_kaohsiung.py            # Crear contratos
    python scripts/create_employee_contracts_kaohsiung.py --factory "本社工場"  # Fábrica específica
"""
import argparse
import sys
from pathlib import Path
from datetime import date, time, datetime, timedelta
from decimal import Decimal
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from app.core.database import SessionLocal, engine
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


# ========================================
# CONFIGURACIÓN
# ========================================

# Período de búsqueda de empleados
HIRE_DATE_START = date(2025, 3, 1)  # Desde marzo 2025
HIRE_DATE_END = date(2025, 9, 30)   # Hasta septiembre 2025

# Fecha fin de todos los contratos
CONTRACT_END_DATE = date(2025, 9, 30)

# Nombre de empresa a buscar
COMPANY_NAME_PATTERN = "高雄工業"

# Datos UNS Kikaku (派遣元)
UNS_KIKAKU_DATA = {
    "responsible_person": {
        "department": "営業部",
        "position": "取締役",
        "name": "ブウ ティ サウ",
        "phone": "052-938-8840",
        "license_number": "派23-123456"
    },
    "complaint_handler": {
        "department": "営業部",
        "position": "取締役部長",
        "name": "中山 欣英",
        "phone": "052-938-8840"
    }
}

# Condiciones de trabajo predeterminadas
DEFAULT_WORK_CONDITIONS = {
    "work_days": ["月", "火", "水", "木", "金"],
    "work_start_time": time(7, 0),   # 07:00
    "work_end_time": time(15, 30),   # 15:30
    "break_time_minutes": 45,
    "overtime_max_hours_day": Decimal("3.0"),
    "overtime_max_hours_month": Decimal("42.0"),
    "holiday_work_max_days": 2,
    "welfare_facilities": ["食堂", "更衣室", "休憩室", "駐車場"],
    "safety_measures": "派遣先の安全衛生規程に従い、必要な保護具を着用すること",
    "termination_measures": "30日前までに書面にて通知。派遣労働者の雇用安定に努める。"
}


def generate_contract_number(db, start_date: date) -> str:
    """
    Generate a unique contract number.
    Format: KOB-YYYYMM-XXXX (e.g., KOB-202503-0001)
    """
    prefix = f"KOB-{start_date.strftime('%Y%m')}-"

    # Get the latest contract number for this month
    latest = (
        db.query(KobetsuKeiyakusho)
        .filter(KobetsuKeiyakusho.contract_number.like(f"{prefix}%"))
        .order_by(KobetsuKeiyakusho.contract_number.desc())
        .first()
    )

    if latest:
        current_seq = int(latest.contract_number.split("-")[-1])
        next_seq = current_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:04d}"


def calculate_overtime_rate(hourly_rate: Decimal) -> Decimal:
    """Calculate overtime rate (1.25x base rate)."""
    return hourly_rate * Decimal("1.25")


def calculate_night_rate(hourly_rate: Decimal) -> Decimal:
    """Calculate night shift rate (1.2x base rate)."""
    return hourly_rate * Decimal("1.2")


def calculate_holiday_rate(hourly_rate: Decimal) -> Decimal:
    """Calculate holiday rate (1.5x base rate)."""
    return hourly_rate * Decimal("1.5")


def load_factory_config(factory_id: str) -> dict | None:
    """
    Load factory configuration from JSON file.
    """
    config_dir = Path(__file__).resolve().parent.parent.parent / "BASEDATEJP" / "config" / "factories"

    # Try direct match
    json_path = config_dir / f"{factory_id}.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Try variations
    for json_file in config_dir.glob(f"*{factory_id.split('_')[0]}*.json"):
        if not json_file.name.startswith("backup"):
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)

    return None


def find_factories(db, pattern: str = COMPANY_NAME_PATTERN, plant_name: str = None) -> list:
    """
    Find factories matching the company name pattern.
    """
    query = db.query(Factory).filter(
        Factory.company_name.ilike(f"%{pattern}%"),
        Factory.is_active == True
    )

    if plant_name:
        query = query.filter(Factory.plant_name.ilike(f"%{plant_name}%"))

    return query.all()


def find_eligible_employees(db, factory_ids: list, start_date: date, end_date: date) -> list:
    """
    Find employees hired between dates and assigned to given factories.
    """
    return (
        db.query(Employee)
        .filter(
            and_(
                Employee.status == "active",
                Employee.hire_date >= start_date,
                Employee.hire_date <= end_date,
                or_(
                    Employee.factory_id.in_(factory_ids),
                    Employee.company_name.ilike(f"%{COMPANY_NAME_PATTERN}%")
                )
            )
        )
        .order_by(Employee.hire_date)
        .all()
    )


def check_existing_contract(db, employee_id: int, factory_id: int, start_date: date, end_date: date) -> bool:
    """
    Check if employee already has a contract for this period.
    """
    existing = (
        db.query(KobetsuEmployee)
        .join(KobetsuKeiyakusho)
        .filter(
            KobetsuEmployee.employee_id == employee_id,
            KobetsuKeiyakusho.factory_id == factory_id,
            KobetsuKeiyakusho.dispatch_start_date <= end_date,
            KobetsuKeiyakusho.dispatch_end_date >= start_date,
            KobetsuKeiyakusho.status.in_(["draft", "active"])
        )
        .first()
    )
    return existing is not None


def get_line_info(factory: Factory, employee: Employee) -> dict:
    """
    Get line information for an employee from factory lines.
    """
    # Try to match by line_name
    if employee.line_name:
        for line in factory.lines:
            if line.line_name and employee.line_name in line.line_name:
                return {
                    "department": line.department or factory.plant_name,
                    "line_name": line.line_name,
                    "supervisor_department": line.supervisor_department or line.department or "",
                    "supervisor_position": line.supervisor_position or "係長",
                    "supervisor_name": line.supervisor_name or "",
                    "job_description": line.job_description or "",
                    "hourly_rate": line.hourly_rate
                }

    # Default to first line or factory defaults
    if factory.lines:
        line = factory.lines[0]
        return {
            "department": line.department or factory.plant_name,
            "line_name": line.line_name or "",
            "supervisor_department": line.supervisor_department or "",
            "supervisor_position": line.supervisor_position or "係長",
            "supervisor_name": line.supervisor_name or "",
            "job_description": line.job_description or "製造業務",
            "hourly_rate": line.hourly_rate
        }

    return {
        "department": factory.plant_name,
        "line_name": "",
        "supervisor_department": "",
        "supervisor_position": "課長",
        "supervisor_name": "",
        "job_description": "製造業務",
        "hourly_rate": None
    }


def create_contract_for_employee(
    db,
    factory: Factory,
    employee: Employee,
    factory_config: dict | None,
    dry_run: bool = False
) -> dict:
    """
    Create a contract for a single employee.
    Returns dict with contract info or error.
    """
    # Dates
    dispatch_start = max(employee.hire_date, HIRE_DATE_START)
    dispatch_end = CONTRACT_END_DATE
    contract_date = dispatch_start - timedelta(days=5)  # 5 days before start

    # Check existing contract
    if check_existing_contract(db, employee.id, factory.id, dispatch_start, dispatch_end):
        return {
            "status": "skipped",
            "reason": "Contract already exists for this period",
            "employee": employee.employee_number
        }

    # Get line info
    line_info = get_line_info(factory, employee)

    # Determine rates
    hourly_rate = employee.hourly_rate or line_info["hourly_rate"] or Decimal("1650")
    overtime_rate = calculate_overtime_rate(hourly_rate)
    night_rate = calculate_night_rate(hourly_rate)
    holiday_rate = calculate_holiday_rate(hourly_rate)

    # Supervisor info
    supervisor_dept = line_info["supervisor_department"] or factory.plant_name
    supervisor_pos = line_info["supervisor_position"] or "係長"
    supervisor_name = line_info["supervisor_name"]

    # If no supervisor from line, try from config
    if not supervisor_name and factory_config:
        lines = factory_config.get("lines", [])
        for line_cfg in lines:
            assignment = line_cfg.get("assignment", {})
            if assignment.get("line") == employee.line_name:
                sup = assignment.get("supervisor", {})
                supervisor_dept = sup.get("department") or supervisor_dept
                supervisor_name = sup.get("name", "")
                break
        if not supervisor_name and lines:
            sup = lines[0].get("assignment", {}).get("supervisor", {})
            supervisor_name = sup.get("name", "係長 担当者")

    if not supervisor_name:
        supervisor_name = "係長 担当者"

    # Work content
    work_content = line_info["job_description"] or employee.position or "製造業務"
    if len(work_content) < 10:
        work_content = f"{work_content}。製造ライン作業、品質検査、設備点検補助作業。"

    # Complaint contacts
    haken_moto_contact = {
        "department": UNS_KIKAKU_DATA["complaint_handler"]["department"],
        "position": UNS_KIKAKU_DATA["complaint_handler"]["position"],
        "name": UNS_KIKAKU_DATA["complaint_handler"]["name"],
        "phone": UNS_KIKAKU_DATA["complaint_handler"]["phone"]
    }

    haken_saki_contact = {
        "department": factory.client_complaint_department or "人事部",
        "position": factory.client_complaint_position or "部長",
        "name": factory.client_complaint_name or "担当者",
        "phone": factory.client_complaint_phone or factory.company_phone or "000-0000-0000"
    }

    # Fix phone format if needed
    for contact in [haken_moto_contact, haken_saki_contact]:
        if contact["phone"] and not "-" in contact["phone"]:
            phone = contact["phone"]
            if len(phone) == 10:
                contact["phone"] = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            elif len(phone) == 11:
                contact["phone"] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"

    # Manager info
    haken_moto_manager = {
        "department": UNS_KIKAKU_DATA["responsible_person"]["department"],
        "position": UNS_KIKAKU_DATA["responsible_person"]["position"],
        "name": UNS_KIKAKU_DATA["responsible_person"]["name"],
        "phone": UNS_KIKAKU_DATA["responsible_person"]["phone"],
        "license_number": UNS_KIKAKU_DATA["responsible_person"].get("license_number", "")
    }

    haken_saki_manager = {
        "department": factory.client_responsible_department or factory.plant_name,
        "position": factory.client_responsible_position or "部長",
        "name": factory.client_responsible_name or "担当者",
        "phone": factory.client_responsible_phone or factory.company_phone or "000-0000-0000",
        "license_number": ""
    }

    # Generate contract number
    contract_number = generate_contract_number(db, dispatch_start)

    if dry_run:
        return {
            "status": "would_create",
            "contract_number": contract_number,
            "employee_number": employee.employee_number,
            "employee_name": employee.full_name_kana or employee.full_name_kanji,
            "factory": f"{factory.company_name} {factory.plant_name}",
            "dispatch_start": str(dispatch_start),
            "dispatch_end": str(dispatch_end),
            "hourly_rate": str(hourly_rate),
            "work_content": work_content[:50] + "..." if len(work_content) > 50 else work_content
        }

    # Create the contract
    contract = KobetsuKeiyakusho(
        contract_number=contract_number,
        factory_id=factory.id,
        contract_date=contract_date,
        dispatch_start_date=dispatch_start,
        dispatch_end_date=dispatch_end,
        work_content=work_content,
        responsibility_level="通常業務",
        worksite_name=f"{factory.company_name} {factory.plant_name}",
        worksite_address=factory.plant_address or factory.company_address or "住所未登録",
        organizational_unit=line_info["department"],
        supervisor_department=supervisor_dept,
        supervisor_position=supervisor_pos,
        supervisor_name=supervisor_name,
        work_days=DEFAULT_WORK_CONDITIONS["work_days"],
        work_start_time=DEFAULT_WORK_CONDITIONS["work_start_time"],
        work_end_time=DEFAULT_WORK_CONDITIONS["work_end_time"],
        break_time_minutes=DEFAULT_WORK_CONDITIONS["break_time_minutes"],
        overtime_max_hours_day=DEFAULT_WORK_CONDITIONS["overtime_max_hours_day"],
        overtime_max_hours_month=DEFAULT_WORK_CONDITIONS["overtime_max_hours_month"],
        holiday_work_max_days=DEFAULT_WORK_CONDITIONS["holiday_work_max_days"],
        safety_measures=DEFAULT_WORK_CONDITIONS["safety_measures"],
        haken_moto_complaint_contact=haken_moto_contact,
        haken_saki_complaint_contact=haken_saki_contact,
        hourly_rate=hourly_rate,
        overtime_rate=overtime_rate,
        night_shift_rate=night_rate,
        holiday_rate=holiday_rate,
        welfare_facilities=DEFAULT_WORK_CONDITIONS["welfare_facilities"],
        haken_moto_manager=haken_moto_manager,
        haken_saki_manager=haken_saki_manager,
        termination_measures=DEFAULT_WORK_CONDITIONS["termination_measures"],
        is_kyotei_taisho=True,
        is_direct_hire_prevention=False,
        is_mukeiko_60over_only=False,
        number_of_workers=1,
        status="draft",
        notes=f"Auto-generated for employee {employee.employee_number} ({employee.full_name_kana or employee.full_name_kanji})",
        created_by=1
    )

    db.add(contract)
    db.flush()  # Get the contract ID

    # Create employee association
    employee_link = KobetsuEmployee(
        kobetsu_keiyakusho_id=contract.id,
        employee_id=employee.id,
        hourly_rate=employee.hourly_rate,
        individual_start_date=dispatch_start,
        individual_end_date=dispatch_end,
        is_indefinite_employment=employee.is_indefinite_employment
    )
    db.add(employee_link)

    return {
        "status": "created",
        "contract_id": contract.id,
        "contract_number": contract_number,
        "employee_number": employee.employee_number,
        "employee_name": employee.full_name_kana or employee.full_name_kanji,
        "factory": f"{factory.company_name} {factory.plant_name}",
        "dispatch_start": str(dispatch_start),
        "dispatch_end": str(dispatch_end),
        "hourly_rate": str(hourly_rate)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create contracts for 高雄工業 employees (March-September 2025)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without creating contracts"
    )
    parser.add_argument(
        "--factory",
        type=str,
        help="Filter by specific plant name (e.g., '本社工場')"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-03-01",
        help="Start date for hire_date filter (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-09-30",
        help="End date for hire_date filter (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Parse dates
    global HIRE_DATE_START, HIRE_DATE_END
    if args.start_date:
        HIRE_DATE_START = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        HIRE_DATE_END = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    print("\n" + "=" * 70)
    print("🏭 高雄工業 契約作成スクリプト")
    print("   Kaohsiung Kogyo Contract Creation Script")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (シミュレーション)' if args.dry_run else 'LIVE (実行)'}")
    print(f"Period: {HIRE_DATE_START} to {HIRE_DATE_END}")
    print(f"Contract End Date: {CONTRACT_END_DATE}")
    if args.factory:
        print(f"Factory Filter: {args.factory}")
    print("=" * 70 + "\n")

    db = SessionLocal()
    results = {
        "created": [],
        "skipped": [],
        "errors": [],
        "would_create": []
    }

    try:
        # Step 1: Find factories
        print("📍 Step 1: Finding factories...")
        factories = find_factories(db, COMPANY_NAME_PATTERN, args.factory)

        if not factories:
            print(f"❌ No factories found matching '{COMPANY_NAME_PATTERN}'")
            print("\nAvailable factories in database:")
            all_factories = db.query(Factory).filter(Factory.is_active == True).limit(20).all()
            for f in all_factories:
                print(f"  - {f.company_name} {f.plant_name} (ID: {f.id})")
            return

        print(f"✅ Found {len(factories)} factory(s):\n")
        for f in factories:
            print(f"  [{f.id}] {f.company_name} - {f.plant_name}")
            print(f"      Address: {f.plant_address or f.company_address or 'N/A'}")
            print(f"      Lines: {len(f.lines)} configured")

        factory_ids = [f.id for f in factories]

        # Step 2: Find eligible employees
        print(f"\n📋 Step 2: Finding employees hired between {HIRE_DATE_START} and {HIRE_DATE_END}...")
        employees = find_eligible_employees(db, factory_ids, HIRE_DATE_START, HIRE_DATE_END)

        if not employees:
            print(f"❌ No eligible employees found")
            print("\nSearching all employees in these factories...")
            all_emp = db.query(Employee).filter(
                or_(
                    Employee.factory_id.in_(factory_ids),
                    Employee.company_name.ilike(f"%{COMPANY_NAME_PATTERN}%")
                )
            ).limit(10).all()
            for e in all_emp:
                print(f"  - {e.employee_number}: {e.full_name_kana or e.full_name_kanji} (hired: {e.hire_date})")
            return

        print(f"✅ Found {len(employees)} eligible employee(s):\n")
        print(f"  {'No.':<6} {'社員番号':<12} {'氏名':<20} {'入社日':<12} {'ライン':<15}")
        print("  " + "-" * 65)
        for i, e in enumerate(employees, 1):
            print(f"  {i:<6} {e.employee_number:<12} {(e.full_name_kana or e.full_name_kanji)[:18]:<20} {str(e.hire_date):<12} {(e.line_name or 'N/A')[:15]:<15}")

        # Step 3: Create contracts
        print(f"\n📝 Step 3: Creating contracts...")
        print("-" * 70)

        for employee in employees:
            # Find matching factory
            factory = None
            for f in factories:
                if employee.factory_id == f.id:
                    factory = f
                    break

            if not factory:
                # Try by company name
                for f in factories:
                    if employee.company_name and f.company_name in employee.company_name:
                        factory = f
                        break

            if not factory:
                factory = factories[0]  # Default to first

            # Load config
            factory_config = load_factory_config(factory.factory_id)

            try:
                result = create_contract_for_employee(
                    db, factory, employee, factory_config, args.dry_run
                )
                results[result["status"]].append(result)

                status_icon = "✅" if result["status"] in ["created", "would_create"] else "⏭️"
                print(f"{status_icon} {result['employee_number']}: {result.get('contract_number', 'N/A')} - {result['status']}")

            except Exception as e:
                error_result = {
                    "status": "error",
                    "employee_number": employee.employee_number,
                    "error": str(e)
                }
                results["errors"].append(error_result)
                print(f"❌ {employee.employee_number}: ERROR - {str(e)[:50]}")

        # Commit if not dry run
        if not args.dry_run:
            db.commit()
            print("\n✅ Changes committed to database")
        else:
            print("\n⚠️  DRY RUN - No changes made to database")

        # Summary
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"  Contracts created:    {len(results['created'])}")
        print(f"  Would create:         {len(results['would_create'])}")
        print(f"  Skipped (existing):   {len(results['skipped'])}")
        print(f"  Errors:               {len(results['errors'])}")
        print("=" * 70)

        # List created contracts
        if results["created"]:
            print("\n📋 Created Contracts:")
            print(f"  {'Contract #':<18} {'Employee':<12} {'Period':<25} {'Rate':<10}")
            print("  " + "-" * 65)
            for r in results["created"]:
                print(f"  {r['contract_number']:<18} {r['employee_number']:<12} {r['dispatch_start']} - {r['dispatch_end']} ¥{r['hourly_rate']}")

        if results["would_create"]:
            print("\n📋 Would Create (Dry Run):")
            print(f"  {'Contract #':<18} {'Employee':<12} {'Period':<25} {'Rate':<10}")
            print("  " + "-" * 65)
            for r in results["would_create"]:
                print(f"  {r['contract_number']:<18} {r['employee_number']:<12} {r['dispatch_start']} - {r['dispatch_end']} ¥{r['hourly_rate']}")

        if results["skipped"]:
            print("\n⏭️  Skipped:")
            for r in results["skipped"]:
                print(f"  - {r['employee']}: {r['reason']}")

        if results["errors"]:
            print("\n❌ Errors:")
            for r in results["errors"]:
                print(f"  - {r['employee_number']}: {r['error']}")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
