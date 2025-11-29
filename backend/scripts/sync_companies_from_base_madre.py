"""
Sync Companies and Plants from Base Madre API

This script connects to Base Madre API and syncs companies and plants data
to the local Kobetsu database.

Usage:
    python scripts/sync_companies_from_base_madre.py --dry-run
    python scripts/sync_companies_from_base_madre.py
    python scripts/sync_companies_from_base_madre.py --api-key YOUR_API_KEY
"""
import sys
import os
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Company, Plant, Jigyosho


# Base Madre API configuration
BASE_MADRE_API_URL = os.getenv("BASE_MADRE_API_URL", "http://localhost:5000/api/v1")
BASE_MADRE_API_KEY = os.getenv("BASE_MADRE_API_KEY", "")


def get_base_madre_headers(api_key: str = None) -> dict:
    """Get headers for Base Madre API requests"""
    key = api_key or BASE_MADRE_API_KEY
    if not key:
        print("⚠️  Warning: No API key provided. Requests may fail.")
        return {}
    return {"X-API-Key": key}


def fetch_companies_from_base_madre(api_key: str = None) -> list:
    """
    Fetch all companies from Base Madre API

    Returns:
        list: List of company dictionaries
    """
    print("\n" + "="*60)
    print("FETCHING COMPANIES FROM BASE MADRE")
    print("="*60)

    url = f"{BASE_MADRE_API_URL}/companies"
    headers = get_base_madre_headers(api_key)

    try:
        print(f"GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("success"):
            companies = data.get("data", [])
            print(f"✅ Fetched {len(companies)} companies from Base Madre")
            return companies
        else:
            print(f"❌ API returned success=False: {data}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching companies from Base Madre: {e}")
        print(f"   URL: {url}")
        print(f"   Make sure Base Madre API is running on {BASE_MADRE_API_URL}")
        return []


def fetch_plants_from_base_madre(api_key: str = None, company_id: int = None) -> list:
    """
    Fetch plants from Base Madre API

    Args:
        api_key: API key for authentication
        company_id: Optional company ID to filter plants

    Returns:
        list: List of plant dictionaries
    """
    print("\n" + "="*60)
    print("FETCHING PLANTS FROM BASE MADRE")
    print("="*60)

    url = f"{BASE_MADRE_API_URL}/plants"
    if company_id:
        url += f"?company_id={company_id}"

    headers = get_base_madre_headers(api_key)

    try:
        print(f"GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("success"):
            plants = data.get("data", [])
            print(f"✅ Fetched {len(plants)} plants from Base Madre")
            return plants
        else:
            print(f"❌ API returned success=False: {data}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching plants from Base Madre: {e}")
        print(f"   URL: {url}")
        return []


def sync_companies(db: Session, companies_data: list, dry_run: bool = True) -> dict:
    """
    Sync companies from Base Madre to local database

    Args:
        db: Database session
        companies_data: List of company dictionaries from Base Madre
        dry_run: If True, don't commit changes

    Returns:
        dict: Statistics {created, updated, skipped}
    """
    print("\n" + "="*60)
    print("SYNCING COMPANIES TO LOCAL DATABASE")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("="*60 + "\n")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for company_data in companies_data:
        base_madre_id = company_data.get("company_id")
        if not base_madre_id:
            print(f"⚠️  Skipping company without ID: {company_data.get('name', 'Unknown')}")
            stats["skipped"] += 1
            continue

        try:
            # Check if company already exists
            existing = db.query(Company).filter(
                Company.base_madre_company_id == base_madre_id
            ).first()

            if existing:
                # Update existing company
                existing.name = company_data.get("name", existing.name)
                existing.name_kana = company_data.get("name_kana")
                existing.address = company_data.get("address")
                existing.phone = company_data.get("phone")
                existing.fax = company_data.get("fax")
                existing.email = company_data.get("email")
                existing.website = company_data.get("website")
                existing.responsible_department = company_data.get("responsible_department")
                existing.responsible_name = company_data.get("responsible_name")
                existing.responsible_phone = company_data.get("responsible_phone")
                existing.notes = company_data.get("notes")
                existing.is_active = company_data.get("is_active", True)
                existing.last_synced_at = datetime.utcnow()

                print(f"📝 Updated: {existing.name} (Base Madre ID: {base_madre_id})")
                stats["updated"] += 1

            else:
                # Create new company
                new_company = Company(
                    name=company_data.get("name"),
                    name_kana=company_data.get("name_kana"),
                    address=company_data.get("address"),
                    phone=company_data.get("phone"),
                    fax=company_data.get("fax"),
                    email=company_data.get("email"),
                    website=company_data.get("website"),
                    responsible_department=company_data.get("responsible_department"),
                    responsible_name=company_data.get("responsible_name"),
                    responsible_phone=company_data.get("responsible_phone"),
                    notes=company_data.get("notes"),
                    is_active=company_data.get("is_active", True),
                    base_madre_company_id=base_madre_id,
                    last_synced_at=datetime.utcnow()
                )
                db.add(new_company)
                print(f"✨ Created: {new_company.name} (Base Madre ID: {base_madre_id})")
                stats["created"] += 1

        except Exception as e:
            print(f"❌ Error processing company {base_madre_id}: {e}")
            stats["errors"] += 1
            continue

    if not dry_run:
        db.commit()
        print(f"\n✅ Changes committed to database")
    else:
        db.rollback()
        print(f"\n⚠️  DRY RUN - No changes were saved")

    return stats


def sync_plants(db: Session, plants_data: list, dry_run: bool = True) -> dict:
    """
    Sync plants from Base Madre to local database

    Args:
        db: Database session
        plants_data: List of plant dictionaries from Base Madre
        dry_run: If True, don't commit changes

    Returns:
        dict: Statistics {created, updated, skipped}
    """
    print("\n" + "="*60)
    print("SYNCING PLANTS TO LOCAL DATABASE")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("="*60 + "\n")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for plant_data in plants_data:
        base_madre_id = plant_data.get("plant_id")
        if not base_madre_id:
            print(f"⚠️  Skipping plant without ID: {plant_data.get('plant_name', 'Unknown')}")
            stats["skipped"] += 1
            continue

        try:
            # Find corresponding company in local DB
            base_madre_company_id = plant_data.get("company_id")
            local_company = db.query(Company).filter(
                Company.base_madre_company_id == base_madre_company_id
            ).first()

            if not local_company:
                print(f"⚠️  Skipping plant {plant_data.get('plant_name')}: Company ID {base_madre_company_id} not found in local DB")
                stats["skipped"] += 1
                continue

            # Check if plant already exists
            existing = db.query(Plant).filter(
                Plant.base_madre_plant_id == base_madre_id
            ).first()

            if existing:
                # Update existing plant
                existing.company_id = local_company.company_id
                existing.plant_name = plant_data.get("plant_name", existing.plant_name)
                existing.plant_code = plant_data.get("plant_code")
                existing.plant_address = plant_data.get("plant_address")
                existing.plant_phone = plant_data.get("plant_phone")
                existing.manager_name = plant_data.get("manager_name")
                existing.capacity = plant_data.get("capacity")
                existing.is_active = plant_data.get("is_active", True)
                existing.last_synced_at = datetime.utcnow()

                print(f"📝 Updated: {existing.plant_name} @ {local_company.name} (Base Madre ID: {base_madre_id})")
                stats["updated"] += 1

            else:
                # Create new plant
                new_plant = Plant(
                    company_id=local_company.company_id,
                    plant_name=plant_data.get("plant_name"),
                    plant_code=plant_data.get("plant_code"),
                    plant_address=plant_data.get("plant_address"),
                    plant_phone=plant_data.get("plant_phone"),
                    manager_name=plant_data.get("manager_name"),
                    capacity=plant_data.get("capacity"),
                    is_active=plant_data.get("is_active", True),
                    base_madre_plant_id=base_madre_id,
                    last_synced_at=datetime.utcnow()
                )
                db.add(new_plant)
                print(f"✨ Created: {new_plant.plant_name} @ {local_company.name} (Base Madre ID: {base_madre_id})")
                stats["created"] += 1

        except Exception as e:
            print(f"❌ Error processing plant {base_madre_id}: {e}")
            stats["errors"] += 1
            continue

    if not dry_run:
        db.commit()
        print(f"\n✅ Changes committed to database")
    else:
        db.rollback()
        print(f"\n⚠️  DRY RUN - No changes were saved")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Sync companies and plants from Base Madre API to Kobetsu database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Base Madre API key (overrides env variable)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="Base Madre API URL (overrides env variable)"
    )
    parser.add_argument(
        "--companies-only",
        action="store_true",
        help="Only sync companies, skip plants"
    )
    parser.add_argument(
        "--plants-only",
        action="store_true",
        help="Only sync plants, skip companies"
    )

    args = parser.parse_args()

    # Override globals if provided
    global BASE_MADRE_API_URL
    if args.api_url:
        BASE_MADRE_API_URL = args.api_url

    print("\n" + "="*60)
    print("SYNC COMPANIES & PLANTS FROM BASE MADRE")
    print("="*60)
    print(f"API URL: {BASE_MADRE_API_URL}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    db = SessionLocal()

    try:
        total_stats = {
            "companies": {"created": 0, "updated": 0, "skipped": 0, "errors": 0},
            "plants": {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        }

        # Sync companies
        if not args.plants_only:
            companies_data = fetch_companies_from_base_madre(args.api_key)
            if companies_data:
                total_stats["companies"] = sync_companies(db, companies_data, args.dry_run)
            else:
                print("⚠️  No companies fetched, skipping sync")

        # Sync plants
        if not args.companies_only:
            plants_data = fetch_plants_from_base_madre(args.api_key)
            if plants_data:
                total_stats["plants"] = sync_plants(db, plants_data, args.dry_run)
            else:
                print("⚠️  No plants fetched, skipping sync")

        # Print summary
        print("\n" + "="*60)
        print("SYNC SUMMARY")
        print("="*60)
        print(f"\nCompanies:")
        print(f"  ✨ Created: {total_stats['companies']['created']}")
        print(f"  📝 Updated: {total_stats['companies']['updated']}")
        print(f"  ⚠️  Skipped: {total_stats['companies']['skipped']}")
        print(f"  ❌ Errors:  {total_stats['companies']['errors']}")
        print(f"\nPlants:")
        print(f"  ✨ Created: {total_stats['plants']['created']}")
        print(f"  📝 Updated: {total_stats['plants']['updated']}")
        print(f"  ⚠️  Skipped: {total_stats['plants']['skipped']}")
        print(f"  ❌ Errors:  {total_stats['plants']['errors']}")
        print("\n" + "="*60)

        if args.dry_run:
            print("⚠️  DRY RUN MODE - No changes were saved to database")
        else:
            print("✅ SYNC COMPLETE - All changes saved to database")

    except Exception as e:
        print(f"\n❌ Fatal error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
