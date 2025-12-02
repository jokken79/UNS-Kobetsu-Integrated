#!/usr/bin/env python3
"""
Link Employees to Factories

Maps employees to their corresponding factories based on company_name matching.
Uses fuzzy matching to handle naming variations.

Usage:
    python scripts/link_employees_to_factories.py --dry-run
    python scripts/link_employees_to_factories.py
"""
import argparse
import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.employee import Employee
from app.models.factory import Factory, FactoryLine


# Manual mapping for employee company_name -> (factory_company, factory_plant)
# This handles cases where automatic matching would fail
MANUAL_MAPPING = {
    # 高雄工業 variations
    "高雄工業 岡山": ("高雄工業株式会社", "岡山工場"),
    "高雄工業 本社": ("高雄工業株式会社", "本社工場"),
    "高雄工業 海南第一": ("高雄工業株式会社", "海南第一工場"),
    "高雄工業 海南第二": ("高雄工業株式会社", "海南第二工場"),
    "高雄工業 静岡": ("高雄工業株式会社", "静岡工場"),

    # 加藤木材工業
    "加藤木材工業 本社": ("加藤木材工業株式会社", "本社工場"),
    "加藤木材工業 春日井": ("加藤木材工業株式会社", "春日井工場"),

    # ユアサ工機
    "ユアサ工機 新城": ("ユアサ工機株式会社", "新城工場"),
    "ユアサ工機 御津": ("ユアサ工機株式会社", "本社工場"),  # 御津 = 本社

    # Simple matches
    "瑞陵精機": ("瑞陵精機株式会社", "恵那工場"),
    "三幸技研": ("三幸技研株式会社", "本社工場"),
    "六甲電子": ("六甲電子株式会社", "本社工場"),
    "川原鉄工所": ("株式会社川原鉄工所", "本社工場"),
    "オーツカ": ("株式会社オーツカ", "関ケ原工場"),
    "ピーエムアイ": ("ピーエムアイ有限会社", "本社工場"),
    "セイビテック": ("セイビテック株式会社", ""),

    # Half-width katakana variations
    "ﾃｨｰｹｰｴﾝｼﾞﾆｱﾘﾝｸﾞ": ("ティーケーエンジニアリング株式会社", "海南第二工場"),
    "ﾌｪﾆﾃｯｸｾﾐｺﾝﾀﾞｸﾀｰ 岡山": ("フェニテックセミコンダクター(株)", "鹿児島工場"),

    # 美鈴工業
    "美鈴工業 本社": ("株式会社美鈴工業", "本社工場"),
    "美鈴工業 本庄": ("株式会社美鈴工業", "本社工場"),  # 本庄 -> 本社
}

# Additional mappings for newly created factories
MANUAL_MAPPING.update({
    # PATEC
    "PATEC": ("PATEC株式会社", "防府工場"),

    # コーリツ
    "コーリツ 本社": ("株式会社コーリツ", "本社工場"),
    "コーリツ 乙川": ("株式会社コーリツ", "乙川工場"),
    "コーリツ 亀崎": ("株式会社コーリツ", "亀崎工場"),
    "コーリツ 州の崎": ("株式会社コーリツ", "州の崎工場"),

    # プレテック
    "プレテック": ("プレテック株式会社", "本社工場"),

    # ワーク
    "ワーク 堺": ("株式会社ワーク", "堺工場"),
    "ワーク 志紀": ("株式会社ワーク", "志紀工場"),
})

# Companies not in our factory database (will be skipped)
UNMAPPED_COMPANIES = set()


def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    if not name:
        return ""
    # Remove common suffixes
    name = re.sub(r'株式会社|有限会社|\(株\)|（株）', '', name)
    # Remove whitespace
    name = name.strip()
    return name


def find_factory_line(db, factory_id: int, department: str, line_name: str):
    """Find matching factory line based on department and line_name."""
    if not factory_id:
        return None

    query = db.query(FactoryLine).filter(FactoryLine.factory_id == factory_id)

    # Try exact match first
    if department and line_name:
        line = query.filter(
            FactoryLine.department == department,
            FactoryLine.line_name == line_name
        ).first()
        if line:
            return line

    # Try line_name match
    if line_name:
        line = query.filter(FactoryLine.line_name == line_name).first()
        if line:
            return line

    # Try department match
    if department:
        line = query.filter(FactoryLine.department == department).first()
        if line:
            return line

    # Return first available line if no match
    return query.first()


def find_factory_match(db, emp_company_name: str):
    """Find matching factory for employee company_name."""
    if not emp_company_name:
        return None

    emp_company_name = emp_company_name.strip()

    # Check manual mapping first
    if emp_company_name in MANUAL_MAPPING:
        company, plant = MANUAL_MAPPING[emp_company_name]
        factory = db.query(Factory).filter(
            Factory.company_name.contains(normalize_name(company)),
            Factory.plant_name == plant
        ).first()

        if not factory:
            # Try with contains on both
            factory = db.query(Factory).filter(
                Factory.company_name.contains(normalize_name(company))
            ).first()

        return factory

    # Check if unmapped
    if emp_company_name in UNMAPPED_COMPANIES:
        return None

    # Try fuzzy matching
    normalized = normalize_name(emp_company_name)

    # Split by space to get company and plant parts
    parts = emp_company_name.split()
    if len(parts) >= 2:
        company_part = parts[0]
        plant_part = parts[1] if len(parts) > 1 else ""

        # Try to find factory matching both parts
        factory = db.query(Factory).filter(
            Factory.company_name.contains(company_part),
            Factory.plant_name.contains(plant_part)
        ).first()

        if factory:
            return factory

    # Last resort: just match company name
    factory = db.query(Factory).filter(
        Factory.company_name.contains(normalized)
    ).first()

    return factory


def link_employees_to_factories(dry_run: bool = True):
    """Link employees to their factories."""
    print(f"\n{'='*60}")
    print("LINK EMPLOYEES TO FACTORIES")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    db = SessionLocal()

    try:
        # Get all employees without factory_id
        employees = db.query(Employee).filter(
            Employee.company_name.isnot(None),
            Employee.status == 'active'
        ).all()

        print(f"Processing {len(employees)} active employees...\n")

        stats = {
            'matched_factory': 0,
            'matched_line': 0,
            'unmatched': 0,
            'already_linked': 0,
        }

        # Track matches by company
        matches_by_company = defaultdict(list)
        unmatched_companies = set()

        for emp in employees:
            if emp.factory_id and emp.factory_line_id:
                stats['already_linked'] += 1
                continue

            # Find factory if not already linked
            factory = None
            if emp.factory_id:
                factory = db.query(Factory).filter(Factory.id == emp.factory_id).first()
            else:
                factory = find_factory_match(db, emp.company_name)

            if factory:
                if not emp.factory_id:
                    stats['matched_factory'] += 1
                matches_by_company[emp.company_name].append((emp, factory))

                if not dry_run:
                    emp.factory_id = factory.id
                    emp.plant_name = factory.plant_name

                # Find factory line
                factory_line = find_factory_line(
                    db,
                    factory.id,
                    emp.department,
                    emp.line_name
                )

                if factory_line:
                    stats['matched_line'] += 1
                    if not dry_run:
                        emp.factory_line_id = factory_line.id
                        if not emp.department:
                            emp.department = factory_line.department
                        if not emp.line_name:
                            emp.line_name = factory_line.line_name
            else:
                stats['unmatched'] += 1
                unmatched_companies.add(emp.company_name)

        # Print matching results
        print("=" * 60)
        print("MATCHING RESULTS BY COMPANY")
        print("=" * 60)

        for company_name, matches in sorted(matches_by_company.items()):
            factory = matches[0][1]
            print(f"\n{company_name} ({len(matches)} empleados)")
            print(f"  -> {factory.company_name} - {factory.plant_name} (ID: {factory.id})")

        if unmatched_companies:
            print("\n" + "=" * 60)
            print("UNMATCHED COMPANIES (no factory found)")
            print("=" * 60)
            for company in sorted(unmatched_companies):
                count = len([e for e in employees if e.company_name == company])
                print(f"  {company}: {count} empleados")

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Factories linked: {stats['matched_factory']}")
        print(f"Lines linked: {stats['matched_line']}")
        print(f"Employees unmatched: {stats['unmatched']}")
        print(f"Already fully linked: {stats['already_linked']}")

        if dry_run:
            print(f"\n{'='*60}")
            print("DRY RUN - No changes made")
            print("Run without --dry-run to apply changes")
            print(f"{'='*60}\n")
        else:
            db.commit()
            print(f"\n{'='*60}")
            print("CHANGES COMMITTED")
            print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Link employees to their factories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )

    args = parser.parse_args()
    success = link_employees_to_factories(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
