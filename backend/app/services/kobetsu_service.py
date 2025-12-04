"""
Kobetsu Keiyakusho Service
Business logic for individual contract management.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.schemas.kobetsu_keiyakusho import (
    KobetsuKeiyakushoCreate,
    KobetsuKeiyakushoUpdate,
    KobetsuKeiyakushoStats,
)

logger = logging.getLogger(__name__)


class KobetsuService:
    """Service class for Kobetsu Keiyakusho operations."""

    def __init__(self, db: Session):
        self.db = db

    def generate_contract_number(self) -> str:
        """
        Generate a unique contract number.
        Format: KOB-YYYYMM-XXXX (e.g., KOB-202411-0001)
        """
        today = datetime.now()
        prefix = f"KOB-{today.strftime('%Y%m')}-"

        # Get the latest contract number for this month
        latest = (
            self.db.query(KobetsuKeiyakusho)
            .filter(KobetsuKeiyakusho.contract_number.like(f"{prefix}%"))
            .order_by(KobetsuKeiyakusho.contract_number.desc())
            .first()
        )

        if latest:
            # Extract the sequence number and increment
            current_seq = int(latest.contract_number.split("-")[-1])
            next_seq = current_seq + 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:04d}"

    def create(
        self,
        data: KobetsuKeiyakushoCreate,
        created_by: Optional[int] = None
    ) -> KobetsuKeiyakusho:
        """
        Create a new Kobetsu Keiyakusho (individual contract).

        Args:
            data: Contract creation data
            created_by: User ID of the creator

        Returns:
            Created KobetsuKeiyakusho instance
        """
        # Generate contract number
        contract_number = self.generate_contract_number()

        # Prepare complaint contact data
        haken_moto_contact = data.haken_moto_complaint_contact.model_dump()
        haken_saki_contact = data.haken_saki_complaint_contact.model_dump()

        # Prepare manager data
        haken_moto_manager = data.haken_moto_manager.model_dump()
        haken_saki_manager = data.haken_saki_manager.model_dump()

        # Create contract instance
        contract = KobetsuKeiyakusho(
            contract_number=contract_number,
            factory_id=data.factory_id,
            dispatch_assignment_id=data.dispatch_assignment_id,
            contract_date=data.contract_date,
            dispatch_start_date=data.dispatch_start_date,
            dispatch_end_date=data.dispatch_end_date,
            work_content=data.work_content,
            responsibility_level=data.responsibility_level,
            worksite_name=data.worksite_name,
            worksite_address=data.worksite_address,
            organizational_unit=data.organizational_unit,
            supervisor_department=data.supervisor_department,
            supervisor_position=data.supervisor_position,
            supervisor_name=data.supervisor_name,
            work_days=data.work_days,
            work_start_time=data.work_start_time,
            work_end_time=data.work_end_time,
            break_time_minutes=data.break_time_minutes,
            overtime_max_hours_day=data.overtime_max_hours_day,
            overtime_max_hours_month=data.overtime_max_hours_month,
            overtime_max_days_month=data.overtime_max_days_month,
            holiday_work_max_days=data.holiday_work_max_days,
            safety_measures=data.safety_measures,
            haken_moto_complaint_contact=haken_moto_contact,
            haken_saki_complaint_contact=haken_saki_contact,
            hourly_rate=data.hourly_rate,
            overtime_rate=data.overtime_rate,
            night_shift_rate=data.night_shift_rate,
            holiday_rate=data.holiday_rate,
            welfare_facilities=data.welfare_facilities,
            haken_moto_manager=haken_moto_manager,
            haken_saki_manager=haken_saki_manager,
            termination_measures=data.termination_measures,
            is_kyotei_taisho=data.is_kyotei_taisho,
            is_direct_hire_prevention=data.is_direct_hire_prevention,
            is_mukeiko_60over_only=data.is_mukeiko_60over_only,
            number_of_workers=len(data.employee_ids),
            status="draft",
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(contract)
        self.db.flush()  # Get the contract ID

        # Create employee associations
        for employee_id in data.employee_ids:
            employee_link = KobetsuEmployee(
                kobetsu_keiyakusho_id=contract.id,
                employee_id=employee_id,
            )
            self.db.add(employee_link)

        self.db.commit()
        self.db.refresh(contract)

        return contract

    def get_by_id(self, contract_id: int) -> Optional[KobetsuKeiyakusho]:
        """
        Get a contract by ID with eager loading.

        Args:
            contract_id: Contract ID

        Returns:
            KobetsuKeiyakusho instance or None
        """
        return (
            self.db.query(KobetsuKeiyakusho)
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                joinedload(KobetsuKeiyakusho.employees)
            )
            .filter(KobetsuKeiyakusho.id == contract_id)
            .first()
        )

    def get_by_contract_number(self, contract_number: str) -> Optional[KobetsuKeiyakusho]:
        """
        Get a contract by contract number with eager loading.

        Args:
            contract_number: Contract number (e.g., KOB-202411-0001)

        Returns:
            KobetsuKeiyakusho instance or None
        """
        return (
            self.db.query(KobetsuKeiyakusho)
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                joinedload(KobetsuKeiyakusho.employees)
            )
            .filter(KobetsuKeiyakusho.contract_number == contract_number)
            .first()
        )

    def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        factory_id: Optional[int] = None,
        search: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[KobetsuKeiyakusho], int]:
        """
        Get paginated list of contracts with filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            factory_id: Filter by factory
            search: Search in contract number and worksite name
            start_date: Filter contracts starting after this date
            end_date: Filter contracts ending before this date
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Tuple of (list of contracts, total count)
        """
        query = self.db.query(KobetsuKeiyakusho).options(
            joinedload(KobetsuKeiyakusho.factory)
        )

        # Apply filters
        if status:
            query = query.filter(KobetsuKeiyakusho.status == status)

        if factory_id:
            query = query.filter(KobetsuKeiyakusho.factory_id == factory_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    KobetsuKeiyakusho.contract_number.ilike(search_term),
                    KobetsuKeiyakusho.worksite_name.ilike(search_term),
                )
            )

        if start_date:
            query = query.filter(KobetsuKeiyakusho.dispatch_start_date >= start_date)

        if end_date:
            query = query.filter(KobetsuKeiyakusho.dispatch_end_date <= end_date)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(KobetsuKeiyakusho, sort_by, KobetsuKeiyakusho.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        contracts = query.offset(skip).limit(limit).all()

        return contracts, total

    def update(
        self,
        contract_id: int,
        data: KobetsuKeiyakushoUpdate
    ) -> Optional[KobetsuKeiyakusho]:
        """
        Update an existing contract.

        Args:
            contract_id: Contract ID
            data: Update data

        Returns:
            Updated KobetsuKeiyakusho instance or None
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        contract.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def delete(self, contract_id: int) -> bool:
        """
        Delete a contract (soft delete by changing status to cancelled).

        Args:
            contract_id: Contract ID

        Returns:
            True if deleted, False if not found
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return False

        # Soft delete - change status to cancelled
        contract.status = "cancelled"
        contract.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return True

    def hard_delete(self, contract_id: int) -> bool:
        """
        Permanently delete a contract (only for drafts).

        Args:
            contract_id: Contract ID

        Returns:
            True if deleted, False if not found or not a draft
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return False

        if contract.status != "draft":
            return False

        # Delete employee associations first
        self.db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).delete()

        # Delete the contract
        self.db.delete(contract)
        self.db.commit()

        return True

    def activate(self, contract_id: int) -> Optional[KobetsuKeiyakusho]:
        """
        Activate a draft contract.

        Args:
            contract_id: Contract ID

        Returns:
            Activated contract or None
        """
        contract = self.get_by_id(contract_id)
        if not contract or contract.status != "draft":
            return None

        contract.status = "active"
        contract.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def renew(
        self,
        contract_id: int,
        new_end_date: date,
        created_by: Optional[int] = None
    ) -> Optional[KobetsuKeiyakusho]:
        """
        Renew a contract by creating a new one with extended end date.

        Args:
            contract_id: Original contract ID
            new_end_date: New dispatch end date
            created_by: User ID of the creator

        Returns:
            New KobetsuKeiyakusho instance or None
        """
        original = self.get_by_id(contract_id)
        if not original:
            return None

        # Mark original as renewed
        original.status = "renewed"
        original.updated_at = datetime.now(timezone.utc)

        # Get employee IDs from original
        employee_ids = [e.employee_id for e in original.employees]

        # Create renewal with same data but new dates
        new_contract = KobetsuKeiyakusho(
            contract_number=self.generate_contract_number(),
            factory_id=original.factory_id,
            dispatch_assignment_id=original.dispatch_assignment_id,
            contract_date=date.today(),
            dispatch_start_date=original.dispatch_end_date + timedelta(days=1),
            dispatch_end_date=new_end_date,
            work_content=original.work_content,
            responsibility_level=original.responsibility_level,
            worksite_name=original.worksite_name,
            worksite_address=original.worksite_address,
            organizational_unit=original.organizational_unit,
            supervisor_department=original.supervisor_department,
            supervisor_position=original.supervisor_position,
            supervisor_name=original.supervisor_name,
            work_days=original.work_days,
            work_start_time=original.work_start_time,
            work_end_time=original.work_end_time,
            break_time_minutes=original.break_time_minutes,
            overtime_max_hours_day=original.overtime_max_hours_day,
            overtime_max_hours_month=original.overtime_max_hours_month,
            overtime_max_days_month=original.overtime_max_days_month,
            holiday_work_max_days=original.holiday_work_max_days,
            safety_measures=original.safety_measures,
            haken_moto_complaint_contact=original.haken_moto_complaint_contact,
            haken_saki_complaint_contact=original.haken_saki_complaint_contact,
            hourly_rate=original.hourly_rate,
            overtime_rate=original.overtime_rate,
            night_shift_rate=original.night_shift_rate,
            holiday_rate=original.holiday_rate,
            welfare_facilities=original.welfare_facilities,
            haken_moto_manager=original.haken_moto_manager,
            haken_saki_manager=original.haken_saki_manager,
            termination_measures=original.termination_measures,
            is_kyotei_taisho=original.is_kyotei_taisho,
            is_direct_hire_prevention=original.is_direct_hire_prevention,
            is_mukeiko_60over_only=original.is_mukeiko_60over_only,
            number_of_workers=len(employee_ids),
            status="draft",
            notes=f"Renewal of {original.contract_number}",
            created_by=created_by,
        )

        self.db.add(new_contract)
        self.db.flush()

        # Create employee associations
        for emp_id in employee_ids:
            employee_link = KobetsuEmployee(
                kobetsu_keiyakusho_id=new_contract.id,
                employee_id=emp_id,
            )
            self.db.add(employee_link)

        self.db.commit()
        self.db.refresh(new_contract)

        return new_contract

    def get_stats(self, factory_id: Optional[int] = None) -> KobetsuKeiyakushoStats:
        """
        Get contract statistics.

        Args:
            factory_id: Optional filter by factory

        Returns:
            KobetsuKeiyakushoStats instance
        """
        from sqlalchemy import case

        # Build base query with optional factory filter
        base_query = self.db.query(KobetsuKeiyakusho)
        if factory_id:
            base_query = base_query.filter(KobetsuKeiyakusho.factory_id == factory_id)

        # Single optimized query using CASE statements
        thirty_days_later = date.today() + timedelta(days=30)
        today = date.today()

        stats = base_query.with_entities(
            func.count(KobetsuKeiyakusho.id).label("total_contracts"),
            func.sum(
                case(
                    (KobetsuKeiyakusho.status == "active", 1),
                    else_=0
                )
            ).label("active_contracts"),
            func.sum(
                case(
                    (
                        and_(
                            KobetsuKeiyakusho.status == "active",
                            KobetsuKeiyakusho.dispatch_end_date <= thirty_days_later,
                            KobetsuKeiyakusho.dispatch_end_date >= today,
                        ),
                        1
                    ),
                    else_=0
                )
            ).label("expiring_soon"),
            func.sum(
                case(
                    (KobetsuKeiyakusho.status == "expired", 1),
                    else_=0
                )
            ).label("expired_contracts"),
            func.sum(
                case(
                    (KobetsuKeiyakusho.status == "draft", 1),
                    else_=0
                )
            ).label("draft_contracts"),
            func.sum(
                case(
                    (KobetsuKeiyakusho.status == "active", KobetsuKeiyakusho.number_of_workers),
                    else_=0
                )
            ).label("total_workers")
        ).first()

        return KobetsuKeiyakushoStats(
            total_contracts=stats.total_contracts or 0,
            active_contracts=int(stats.active_contracts or 0),
            expiring_soon=int(stats.expiring_soon or 0),
            expired_contracts=int(stats.expired_contracts or 0),
            draft_contracts=int(stats.draft_contracts or 0),
            total_workers=int(stats.total_workers or 0),
        )

    def get_by_factory(self, factory_id: int) -> List[KobetsuKeiyakusho]:
        """Get all contracts for a factory with eager loading."""
        return (
            self.db.query(KobetsuKeiyakusho)
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                joinedload(KobetsuKeiyakusho.employees)
            )
            .filter(KobetsuKeiyakusho.factory_id == factory_id)
            .order_by(KobetsuKeiyakusho.created_at.desc())
            .all()
        )

    def get_by_employee(self, employee_id: int) -> List[KobetsuKeiyakusho]:
        """Get all contracts for an employee with eager loading."""
        return (
            self.db.query(KobetsuKeiyakusho)
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                joinedload(KobetsuKeiyakusho.employees)
            )
            .join(KobetsuEmployee)
            .filter(KobetsuEmployee.employee_id == employee_id)
            .order_by(KobetsuKeiyakusho.created_at.desc())
            .all()
        )

    def get_expiring_contracts(self, days: int = 30) -> List[KobetsuKeiyakusho]:
        """Get contracts expiring within specified days with eager loading."""
        threshold = date.today() + timedelta(days=days)
        return (
            self.db.query(KobetsuKeiyakusho)
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                joinedload(KobetsuKeiyakusho.employees)
            )
            .filter(
                and_(
                    KobetsuKeiyakusho.status == "active",
                    KobetsuKeiyakusho.dispatch_end_date <= threshold,
                    KobetsuKeiyakusho.dispatch_end_date >= date.today(),
                )
            )
            .order_by(KobetsuKeiyakusho.dispatch_end_date.asc())
            .all()
        )

    def update_expired_contracts(self) -> int:
        """
        Update status of expired contracts to 'expired'.
        Should be run as a scheduled task.

        Returns:
            Number of contracts updated
        """
        today = date.today()
        result = (
            self.db.query(KobetsuKeiyakusho)
            .filter(
                and_(
                    KobetsuKeiyakusho.status == "active",
                    KobetsuKeiyakusho.dispatch_end_date < today,
                )
            )
            .update({"status": "expired", "updated_at": datetime.now(timezone.utc)})
        )
        self.db.commit()
        return result

    def sign_contract(
        self,
        contract_id: int,
        pdf_path: str
    ) -> Optional[KobetsuKeiyakusho]:
        """
        Mark a contract as signed and store PDF path.

        Args:
            contract_id: Contract ID
            pdf_path: Path to signed PDF

        Returns:
            Updated contract or None
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return None

        contract.pdf_path = pdf_path
        contract.signed_date = date.today()
        contract.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def add_employee(
        self,
        contract_id: int,
        employee_id: int
    ) -> bool:
        """
        Add an employee to a contract.

        Args:
            contract_id: Contract ID
            employee_id: Employee ID

        Returns:
            True if added, False if failed
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return False

        # Check if already exists
        existing = (
            self.db.query(KobetsuEmployee)
            .filter(
                and_(
                    KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
                    KobetsuEmployee.employee_id == employee_id,
                )
            )
            .first()
        )

        if existing:
            return False

        employee_link = KobetsuEmployee(
            kobetsu_keiyakusho_id=contract_id,
            employee_id=employee_id,
        )
        self.db.add(employee_link)

        # Update worker count
        contract.number_of_workers += 1
        contract.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    def remove_employee(
        self,
        contract_id: int,
        employee_id: int
    ) -> bool:
        """
        Remove an employee from a contract.

        Args:
            contract_id: Contract ID
            employee_id: Employee ID

        Returns:
            True if removed, False if failed
        """
        contract = self.get_by_id(contract_id)
        if not contract:
            return False

        result = (
            self.db.query(KobetsuEmployee)
            .filter(
                and_(
                    KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
                    KobetsuEmployee.employee_id == employee_id,
                )
            )
            .delete()
        )

        if result:
            contract.number_of_workers = max(0, contract.number_of_workers - 1)
            contract.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True

        return False

    def get_employees(self, contract_id: int) -> List[int]:
        """
        Get list of employee IDs for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            List of employee IDs
        """
        employees = (
            self.db.query(KobetsuEmployee.employee_id)
            .filter(KobetsuEmployee.kobetsu_keiyakusho_id == contract_id)
            .all()
        )
        return [e[0] for e in employees]

    def duplicate(
        self,
        contract_id: int,
        created_by: Optional[int] = None
    ) -> Optional[KobetsuKeiyakusho]:
        """
        Create a copy of an existing contract as a draft.

        Args:
            contract_id: Contract ID to duplicate
            created_by: User ID of the creator

        Returns:
            New KobetsuKeiyakusho instance or None
        """
        original = self.get_by_id(contract_id)
        if not original:
            return None

        # Get employee IDs from original
        employee_ids = self.get_employees(contract_id)

        new_contract = KobetsuKeiyakusho(
            contract_number=self.generate_contract_number(),
            factory_id=original.factory_id,
            dispatch_assignment_id=original.dispatch_assignment_id,
            contract_date=date.today(),
            dispatch_start_date=original.dispatch_start_date,
            dispatch_end_date=original.dispatch_end_date,
            work_content=original.work_content,
            responsibility_level=original.responsibility_level,
            worksite_name=original.worksite_name,
            worksite_address=original.worksite_address,
            organizational_unit=original.organizational_unit,
            supervisor_department=original.supervisor_department,
            supervisor_position=original.supervisor_position,
            supervisor_name=original.supervisor_name,
            work_days=original.work_days,
            work_start_time=original.work_start_time,
            work_end_time=original.work_end_time,
            break_time_minutes=original.break_time_minutes,
            overtime_max_hours_day=original.overtime_max_hours_day,
            overtime_max_hours_month=original.overtime_max_hours_month,
            overtime_max_days_month=original.overtime_max_days_month,
            holiday_work_max_days=original.holiday_work_max_days,
            safety_measures=original.safety_measures,
            haken_moto_complaint_contact=original.haken_moto_complaint_contact,
            haken_saki_complaint_contact=original.haken_saki_complaint_contact,
            hourly_rate=original.hourly_rate,
            overtime_rate=original.overtime_rate,
            night_shift_rate=original.night_shift_rate,
            holiday_rate=original.holiday_rate,
            welfare_facilities=original.welfare_facilities,
            haken_moto_manager=original.haken_moto_manager,
            haken_saki_manager=original.haken_saki_manager,
            termination_measures=original.termination_measures,
            is_kyotei_taisho=original.is_kyotei_taisho,
            is_direct_hire_prevention=original.is_direct_hire_prevention,
            is_mukeiko_60over_only=original.is_mukeiko_60over_only,
            number_of_workers=len(employee_ids),
            status="draft",
            notes=f"Copy of {original.contract_number}",
            created_by=created_by,
        )

        self.db.add(new_contract)
        self.db.flush()

        # Create employee associations
        for emp_id in employee_ids:
            employee_link = KobetsuEmployee(
                kobetsu_keiyakusho_id=new_contract.id,
                employee_id=emp_id,
            )
            self.db.add(employee_link)

        self.db.commit()
        self.db.refresh(new_contract)

        return new_contract
