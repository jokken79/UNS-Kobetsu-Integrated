"""
Contract Renewal Service
Handles generating contract renewals based on factory cycles.
"""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.employee import Employee
from app.models.user import User
from app.schemas.kobetsu_keiyakusho import KobetsuKeiyakushoCreate
from app.services.kobetsu_service import KobetsuService
from app.services.contract_date_service import ContractDateService


class ContractRenewalService:
    """Service for generating contract renewals based on factory cycles."""

    # Fields that are copied from previous contract to renewal
    RENEWABLE_FIELDS = {
        'factory_id',
        'work_content',
        'responsibility_level',
        'worksite_name',
        'worksite_address',
        'organizational_unit',
        'supervisor_department',
        'supervisor_position',
        'supervisor_name',
        'work_days',
        'work_start_time',
        'work_end_time',
        'break_time_minutes',
        'hourly_rate',
        'overtime_rate',
        'night_shift_rate',
        'holiday_rate',
        'overtime_max_hours_day',
        'overtime_max_hours_month',
        'overtime_max_days_month',
        'holiday_work_max_days',
        'safety_measures',
        'welfare_facilities',
        'haken_moto_complaint_contact',
        'haken_saki_complaint_contact',
        'haken_moto_manager',
        'haken_saki_manager',
        'is_direct_hire_prevention',
        'is_kyotei_taisho',
        'is_mukeiko_60over_only',
        'termination_measures',
        'notes',
    }

    def __init__(self, db: Session):
        self.db = db
        self.date_service = ContractDateService(db)
        self.kobetsu_service = KobetsuService(db)

    def renew_contract(
        self,
        current_contract_id: int,
        created_by_id: int
    ) -> KobetsuKeiyakusho:
        """
        Generate next contract based on current contract and factory cycle.

        This method:
        1. Validates current contract exists
        2. Validates all employees are still active
        3. Calculates new contract dates based on factory cycle
        4. Copies only whitelisted fields from current contract
        5. Creates new contract with status='draft'
        6. Links to previous contract for audit trail

        Args:
            current_contract_id: ID of contract to renew
            created_by_id: ID of user creating renewal

        Returns:
            New KobetsuKeiyakusho contract

        Raises:
            ValueError: If contract not found, employee resigned, or validation fails
        """
        # Get current contract
        current_contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == current_contract_id
        ).first()

        if not current_contract:
            raise ValueError(f"Contract {current_contract_id} not found")

        # Validate all employees are still active
        employee_ids = [emp.employee_id for emp in current_contract.employees]
        resigned_employees = self.db.query(Employee).filter(
            Employee.id.in_(employee_ids),
            Employee.status == 'resigned'
        ).all()

        if resigned_employees:
            names = ', '.join([f"{e.full_name_kanji} ({e.employee_number})" for e in resigned_employees])
            raise ValueError(f"Cannot renew: employees have resigned: {names}")

        # Calculate new contract dates
        new_start_date, new_end_date = self.date_service.calculate_renewal_dates(current_contract_id)

        # Build renewal data from whitelisted fields
        renewal_data_dict = {}
        for field in self.RENEWABLE_FIELDS:
            if hasattr(current_contract, field):
                value = getattr(current_contract, field)
                renewal_data_dict[field] = value

        # Override with new dates
        renewal_data_dict['dispatch_start_date'] = new_start_date
        renewal_data_dict['dispatch_end_date'] = new_end_date
        renewal_data_dict['employee_ids'] = employee_ids
        renewal_data_dict['contract_date'] = datetime.now().date()

        # Create renewal contract
        renewal_schema = KobetsuKeiyakushoCreate(**renewal_data_dict)
        renewal_contract = self.kobetsu_service.create(renewal_schema, created_by=created_by_id)

        # Link to previous contract for audit trail
        renewal_contract.previous_contract_id = current_contract_id
        self.db.commit()
        self.db.refresh(renewal_contract)

        return renewal_contract

    def get_renewal_info(self, contract_id: int) -> dict:
        """
        Get information about what will be renewed for a contract.

        Used to show preview before renewal.

        Returns:
            Dict with contract info, employees, and calculated new dates
        """
        contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == contract_id
        ).first()

        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        new_start, new_end = self.date_service.calculate_renewal_dates(contract_id)

        # Get employee details
        employees = self.db.query(Employee).filter(
            Employee.id.in_([e.employee_id for e in contract.employees])
        ).all()

        resigned = [e for e in employees if e.status == 'resigned']
        active = [e for e in employees if e.status != 'resigned']

        return {
            'current_contract': {
                'id': contract.id,
                'contract_number': contract.contract_number,
                'dispatch_end_date': str(contract.dispatch_end_date),
            },
            'renewal_info': {
                'dispatch_start_date': str(new_start),
                'dispatch_end_date': str(new_end),
                'duration_days': (new_end - new_start).days + 1,
            },
            'employees': {
                'active': [
                    {
                        'id': e.id,
                        'employee_number': e.employee_number,
                        'full_name': e.full_name_kanji,
                        'status': e.status
                    } for e in active
                ],
                'resigned': [
                    {
                        'id': e.id,
                        'employee_number': e.employee_number,
                        'full_name': e.full_name_kanji,
                        'status': e.status
                    } for e in resigned
                ],
            },
            'fields_to_copy': len(self.RENEWABLE_FIELDS),
            'warnings': [
                f"Will include {len(resigned)} resigned employees" if resigned else None
            ]
        }
