"""
Document Data Service - Converts ORM models to JSON format for document generation.

This service acts as the bridge between database models and document generators.
"""
from datetime import date
from typing import List
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.factory import Factory
from app.models.employee import Employee
from app.schemas.document_data import (
    DocumentDataSchema,
    CompanyInfo,
    PersonInfo,
    WorkSchedule,
    RateInfo,
    EmployeeData,
)
from app.core.config import settings


class DocumentDataService:
    """
    Service for converting database models to document JSON format.

    This provides a clean separation between data storage and document generation.
    """

    @staticmethod
    def _get_dispatch_company_info() -> CompanyInfo:
        """Get dispatch company (UNS Kikaku) info from settings."""
        return CompanyInfo(
            name=settings.COMPANY_NAME,
            name_legal=settings.COMPANY_NAME_LEGAL,
            postal_code=settings.COMPANY_POSTAL_CODE,
            address=settings.COMPANY_ADDRESS,
            tel=settings.COMPANY_TEL,
            fax=settings.COMPANY_FAX,
            email=settings.COMPANY_EMAIL,
            license_number=settings.COMPANY_LICENSE_NUMBER,
        )

    @staticmethod
    def _get_dispatch_manager() -> PersonInfo:
        """Get dispatch origin manager from settings."""
        return PersonInfo(
            name=settings.DISPATCH_MANAGER_NAME,
            position=settings.DISPATCH_MANAGER_POSITION,
            department=settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
            phone=settings.DISPATCH_RESPONSIBLE_PHONE,
        )

    @staticmethod
    def _get_dispatch_complaint_handler() -> PersonInfo:
        """Get complaint handler at dispatch company."""
        return PersonInfo(
            name=settings.DISPATCH_COMPLAINT_NAME,
            position=settings.DISPATCH_COMPLAINT_POSITION,
            department=settings.DISPATCH_COMPLAINT_DEPARTMENT,
            phone=settings.DISPATCH_COMPLAINT_PHONE,
        )

    @staticmethod
    def _factory_to_company_info(factory: Factory) -> CompanyInfo:
        """Convert Factory model to CompanyInfo."""
        return CompanyInfo(
            name=factory.company_name,
            address=factory.company_address or "",
            tel=factory.company_tel or "",
            fax=factory.company_fax,
            email=factory.company_email,
        )

    @staticmethod
    def _create_person_from_data(
        name: str = None,
        department: str = None,
        position: str = None,
        phone: str = None,
    ) -> PersonInfo:
        """Create PersonInfo from individual fields."""
        return PersonInfo(
            name=name or "",
            department=department,
            position=position,
            phone=phone,
        )

    @staticmethod
    def _employee_to_employee_data(employee: Employee) -> EmployeeData:
        """Convert Employee model to EmployeeData."""
        return EmployeeData(
            employee_number=employee.employee_number,
            full_name=employee.full_name_kanji or employee.full_name,
            full_name_kana=employee.full_name_katakana or "",
            gender=employee.gender,
            date_of_birth=employee.date_of_birth,
            nationality=employee.nationality,
            address=employee.current_address,
            phone=employee.phone_number,
        )

    @classmethod
    def from_kobetsu_contract(
        cls,
        contract: KobetsuKeiyakusho,
        db: Session,
    ) -> DocumentDataSchema:
        """
        Convert KobetsuKeiyakusho model to DocumentDataSchema (JSON).

        Args:
            contract: KobetsuKeiyakusho ORM instance
            db: Database session for loading relationships

        Returns:
            DocumentDataSchema ready for document generation
        """
        # Load factory relationship if not loaded
        factory = contract.factory

        # Build schedule
        schedule = WorkSchedule(
            work_days=contract.work_days or ["月", "火", "水", "木", "金"],
            work_start_time=contract.work_start_time,
            work_end_time=contract.work_end_time,
            break_time_minutes=contract.break_time_minutes or 60,
            overtime_max_hours_day=contract.overtime_max_hours_day or 4,
            overtime_max_hours_month=contract.overtime_max_hours_month or 45,
        )

        # Build rates
        rates = RateInfo(
            hourly_rate=contract.hourly_rate or Decimal("1500"),
            overtime_rate=contract.overtime_rate,
            holiday_rate=contract.holiday_work_rate,
            night_shift_rate=contract.night_shift_rate,
        )

        # Build supervisor
        supervisor = cls._create_person_from_data(
            name=contract.supervisor_name,
            department=contract.supervisor_department,
            position=contract.supervisor_position,
        )

        # Build client managers (from contract fields)
        client_manager = cls._create_person_from_data(
            name=contract.haken_saki_manager_name,
            phone=contract.haken_saki_manager_phone,
        )

        client_complaint_handler = cls._create_person_from_data(
            name=contract.haken_saki_complaint_contact_name,
            department=contract.haken_saki_complaint_contact_department,
            phone=contract.haken_saki_complaint_contact_phone,
        )

        # Get employees
        employees_data = []
        if hasattr(contract, 'employees'):
            employees_data = [
                cls._employee_to_employee_data(emp)
                for emp in contract.employees
            ]

        # Build final schema
        return DocumentDataSchema(
            # Contract identification
            contract_number=contract.contract_number,
            contract_date=contract.contract_date or date.today(),
            document_date=date.today(),

            # Dispatch period
            dispatch_start_date=contract.dispatch_start_date,
            dispatch_end_date=contract.dispatch_end_date,

            # Dispatch company (UNS Kikaku)
            dispatch_company=cls._get_dispatch_company_info(),
            dispatch_manager=cls._get_dispatch_manager(),
            dispatch_complaint_handler=cls._get_dispatch_complaint_handler(),

            # Client company
            client_company=cls._factory_to_company_info(factory),
            client_manager=client_manager,
            client_complaint_handler=client_complaint_handler,

            # Worksite details
            worksite_name=contract.worksite_name or factory.factory_name,
            worksite_address=contract.worksite_address or factory.factory_address or "",
            organizational_unit=contract.organizational_unit or factory.department,
            production_line=factory.line,

            # Work content
            work_content=contract.work_content or "",
            responsibility_level=contract.responsibility_level or "通常業務",

            # Supervision
            supervisor=supervisor,

            # Schedule & rates
            schedule=schedule,
            rates=rates,

            # Employees
            employees=employees_data,
            number_of_workers=len(employees_data) or contract.number_of_workers or 1,

            # Safety & welfare
            safety_measures=contract.safety_and_health_measures or "派遣先の安全衛生規程に従う",
            welfare_facilities=contract.welfare_facilities or ["食堂", "更衣室", "休憩室"],

            # Legal compliance
            is_kyotei_taisho=contract.is_kyotei_taisho or False,
            is_mukeiko_60over_only=contract.is_mukeiko_60over_only or False,
            is_direct_hire_prevention=contract.is_direct_hire_prevention or False,

            # Metadata
            notes=contract.notes,
            version="1.0",
        )

    @classmethod
    def to_json_dict(cls, contract: KobetsuKeiyakusho, db: Session) -> dict:
        """
        Convert contract to plain JSON dict (for API responses).

        Args:
            contract: KobetsuKeiyakusho instance
            db: Database session

        Returns:
            Plain dict that can be JSON serialized
        """
        schema = cls.from_kobetsu_contract(contract, db)
        return schema.model_dump(mode='json')

    @classmethod
    def validate_json(cls, json_data: dict) -> DocumentDataSchema:
        """
        Validate JSON data against schema.

        Args:
            json_data: Dictionary to validate

        Returns:
            Validated DocumentDataSchema

        Raises:
            ValidationError: If data doesn't match schema
        """
        return DocumentDataSchema(**json_data)
