"""
API Helper Functions

Common validation and utility functions for API endpoints.
Reduces code duplication and centralizes error handling.
"""
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.employee import Employee
from app.models.factory import Factory


def get_contract_or_404(
    db: Session,
    contract_id: int
) -> KobetsuKeiyakusho:
    """
    Get a contract by ID or raise 404 error.

    Args:
        db: Database session
        contract_id: Contract ID

    Returns:
        KobetsuKeiyakusho instance

    Raises:
        HTTPException: 404 if contract not found
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract with ID {contract_id} not found"
        )

    return contract


def get_employee_or_404(
    db: Session,
    employee_id: int
) -> Employee:
    """
    Get an employee by ID or raise 404 error.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        Employee instance

    Raises:
        HTTPException: 404 if employee not found
    """
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail=f"Employee with ID {employee_id} not found"
        )

    return employee


def get_factory_or_404(
    db: Session,
    factory_id: int
) -> Factory:
    """
    Get a factory by ID or raise 404 error.

    Args:
        db: Database session
        factory_id: Factory ID

    Returns:
        Factory instance

    Raises:
        HTTPException: 404 if factory not found
    """
    factory = db.query(Factory).filter(
        Factory.id == factory_id
    ).first()

    if not factory:
        raise HTTPException(
            status_code=404,
            detail=f"Factory with ID {factory_id} not found"
        )

    return factory


def validate_contract_exists(
    db: Session,
    contract_number: str
) -> Optional[KobetsuKeiyakusho]:
    """
    Check if a contract with given contract number already exists.

    Args:
        db: Database session
        contract_number: Contract number to check

    Returns:
        Existing contract or None
    """
    return db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.contract_number == contract_number
    ).first()


def validate_employee_not_in_contract(
    db: Session,
    contract_id: int,
    employee_id: int
) -> bool:
    """
    Check if an employee is already in a contract.

    Args:
        db: Database session
        contract_id: Contract ID
        employee_id: Employee ID

    Returns:
        True if employee is not in contract, False otherwise
    """
    from app.models.kobetsu_keiyakusho import KobetsuEmployee

    existing = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
        KobetsuEmployee.employee_id == employee_id
    ).first()

    return existing is None


def validate_contract_status(
    contract: KobetsuKeiyakusho,
    allowed_statuses: list[str],
    error_message: str = "Invalid contract status for this operation"
) -> None:
    """
    Validate that contract has one of the allowed statuses.

    Args:
        contract: Contract instance
        allowed_statuses: List of allowed status values
        error_message: Custom error message

    Raises:
        HTTPException: 400 if status is not allowed
    """
    if contract.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"{error_message}. Current status: {contract.status}, allowed: {', '.join(allowed_statuses)}"
        )


def validate_date_range(
    start_date,
    end_date,
    field_name: str = "date"
) -> None:
    """
    Validate that end date is after start date.

    Args:
        start_date: Start date
        end_date: End date
        field_name: Field name for error message

    Raises:
        HTTPException: 400 if date range is invalid
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} range: end date must be after start date"
        )