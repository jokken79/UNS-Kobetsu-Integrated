"""
Employee API Router - 派遣社員 endpoints.

Provides CRUD operations and filtering for dispatch workers.
"""
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.employee import Employee
from app.models.factory import Factory, FactoryLine
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListItem,
    EmployeeStats, EmployeeAssignment, EmployeeForContract
)

router = APIRouter(redirect_slashes=False)


# ========================================
# EMPLOYEE CRUD
# ========================================

@router.get("", response_model=List[EmployeeListItem])
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = Query("active", description="Employee status filter"),
    company_name: Optional[str] = None,
    factory_id: Optional[int] = None,
    nationality: Optional[str] = None,
    visa_expiring_days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of employees with optional filters."""
    query = db.query(Employee)

    # Status filter
    if status:
        query = query.filter(Employee.status == status)

    # Company filter
    if company_name:
        query = query.filter(Employee.company_name == company_name)

    if factory_id:
        query = query.filter(Employee.factory_id == factory_id)

    # Nationality filter
    if nationality:
        query = query.filter(Employee.nationality == nationality)

    # Search filter (name, employee number, kana)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name_kanji.ilike(search_term),
                Employee.full_name_kana.ilike(search_term),
                Employee.employee_number.ilike(search_term)
            )
        )

    # Visa expiring soon filter
    if visa_expiring_days:
        expiry_date = date.today() + timedelta(days=visa_expiring_days)
        query = query.filter(
            Employee.visa_expiry_date.isnot(None),
            Employee.visa_expiry_date <= expiry_date
        )

    employees = query.order_by(
        Employee.company_name,
        Employee.full_name_kana
    ).offset(skip).limit(limit).all()

    return employees


@router.get("/stats", response_model=EmployeeStats)
async def get_employee_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get employee statistics."""
    # Total counts
    total = db.query(func.count(Employee.id)).scalar()
    active = db.query(func.count(Employee.id)).filter(Employee.status == "active").scalar()
    resigned = db.query(func.count(Employee.id)).filter(Employee.status == "resigned").scalar()

    # Visa expiring in 30 days
    expiry_date = date.today() + timedelta(days=30)
    visa_expiring = db.query(func.count(Employee.id)).filter(
        Employee.status == "active",
        Employee.visa_expiry_date.isnot(None),
        Employee.visa_expiry_date <= expiry_date
    ).scalar()

    # Calculate ages for active employees
    today = date.today()
    active_employees_with_dob = db.query(Employee).filter(
        Employee.status == "active",
        Employee.date_of_birth.isnot(None)
    ).all()

    ages = []
    under_18 = 0
    over_60 = 0
    for emp in active_employees_with_dob:
        age = today.year - emp.date_of_birth.year - (
            (today.month, today.day) < (emp.date_of_birth.month, emp.date_of_birth.day)
        )
        ages.append(age)
        if age < 18:
            under_18 += 1
        elif age >= 60:
            over_60 += 1

    average_age = sum(ages) / len(ages) if ages else None

    # By company
    by_company = db.query(
        Employee.company_name,
        func.count(Employee.id).label('count')
    ).filter(
        Employee.status == "active",
        Employee.company_name.isnot(None)
    ).group_by(Employee.company_name).order_by(func.count(Employee.id).desc()).limit(10).all()

    # By nationality
    by_nationality = db.query(
        Employee.nationality,
        func.count(Employee.id).label('count')
    ).filter(
        Employee.status == "active"
    ).group_by(Employee.nationality).order_by(func.count(Employee.id).desc()).all()

    return EmployeeStats(
        total_employees=total or 0,
        active_employees=active or 0,
        resigned_employees=resigned or 0,
        visa_expiring_soon=visa_expiring or 0,
        average_age=average_age,
        under_18_count=under_18,
        over_60_count=over_60,
        by_company=[{"company_name": r.company_name, "count": r.count} for r in by_company],
        by_nationality=[{"nationality": r.nationality or "未設定", "count": r.count} for r in by_nationality]
    )


@router.get("/for-contract", response_model=List[EmployeeForContract])
async def get_employees_for_contract(
    factory_id: Optional[int] = None,
    search: Optional[str] = None,
    exclude_ids: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get employees available for contract assignment.
    Returns minimal info needed for contract selection dropdown.
    """
    query = db.query(Employee).filter(Employee.status == "active")

    if factory_id:
        # Show employees already assigned to this factory
        query = query.filter(Employee.factory_id == factory_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name_kanji.ilike(search_term),
                Employee.full_name_kana.ilike(search_term),
                Employee.employee_number.ilike(search_term)
            )
        )

    if exclude_ids:
        exclude_list = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if exclude_list:
            query = query.filter(~Employee.id.in_(exclude_list))

    employees = query.order_by(Employee.full_name_kana).limit(limit).all()

    result = []
    for emp in employees:
        result.append(EmployeeForContract(
            id=emp.id,
            employee_number=emp.employee_number,
            full_name_kanji=emp.full_name_kanji,
            full_name_kana=emp.full_name_kana,
            display_name=emp.display_name,
            gender=emp.gender,
            age=emp.calculated_age,
            age_category=emp.age_category,
            nationality=emp.nationality or "ベトナム",
            has_employment_insurance=emp.has_employment_insurance,
            has_health_insurance=emp.has_health_insurance,
            has_pension_insurance=emp.has_pension_insurance,
            is_indefinite_employment=emp.is_indefinite_employment
        ))

    return result


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get employee details by ID."""
    employee = db.query(Employee).options(
        joinedload(Employee.factory),
        joinedload(Employee.factory_line)
    ).filter(Employee.id == employee_id).first()

    if not employee:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    response = EmployeeResponse.model_validate(employee)
    response.age = employee.calculated_age
    response.display_name = employee.display_name
    response.is_indefinite_employment = employee.is_indefinite_employment
    response.employment_type_display = employee.employment_type_display
    response.age_category = employee.age_category

    return response


@router.post("/", response_model=EmployeeResponse, status_code=http_status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new employee."""
    # Check for duplicate employee number
    existing = db.query(Employee).filter(
        Employee.employee_number == employee_data.employee_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Employee number '{employee_data.employee_number}' already exists"
        )

    employee = Employee(**employee_data.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)

    return EmployeeResponse.model_validate(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if not employee:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return EmployeeResponse.model_validate(employee)


@router.delete("/{employee_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an employee (soft delete by setting status to resigned)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if not employee:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    employee.status = "resigned"
    employee.termination_date = date.today()
    db.commit()


# ========================================
# ASSIGNMENT ENDPOINT
# ========================================

@router.post("/{employee_id}/assign", response_model=EmployeeResponse)
async def assign_employee_to_factory(
    employee_id: int,
    assignment: EmployeeAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign an employee to a factory/line.
    Updates both factory reference and denormalized fields.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Verify factory exists
    factory = db.query(Factory).filter(Factory.id == assignment.factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    # Update assignment
    employee.factory_id = assignment.factory_id
    employee.factory_line_id = assignment.factory_line_id
    employee.company_name = assignment.company_name or factory.company_name
    employee.plant_name = assignment.plant_name or factory.plant_name
    employee.department = assignment.department
    employee.line_name = assignment.line_name
    employee.position = assignment.position

    # Update rates if provided
    if assignment.hourly_rate is not None:
        employee.hourly_rate = assignment.hourly_rate
    if assignment.billing_rate is not None:
        employee.billing_rate = assignment.billing_rate

    db.commit()
    db.refresh(employee)

    return EmployeeResponse.model_validate(employee)


@router.post("/{employee_id}/unassign", response_model=EmployeeResponse)
async def unassign_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove employee from current factory assignment."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.factory_id = None
    employee.factory_line_id = None
    employee.company_name = None
    employee.plant_name = None
    employee.department = None
    employee.line_name = None

    db.commit()
    db.refresh(employee)

    return EmployeeResponse.model_validate(employee)


# ========================================
# VISA MANAGEMENT
# ========================================

@router.get("/visa/expiring", response_model=List[EmployeeListItem])
async def get_employees_with_expiring_visa(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get employees with visa expiring within specified days."""
    expiry_date = date.today() + timedelta(days=days)

    employees = db.query(Employee).filter(
        Employee.status == "active",
        Employee.visa_expiry_date.isnot(None),
        Employee.visa_expiry_date <= expiry_date,
        Employee.visa_expiry_date >= date.today()
    ).order_by(Employee.visa_expiry_date).all()

    return employees


# ========================================
# BULK OPERATIONS
# ========================================

@router.post("/bulk/assign")
async def bulk_assign_employees(
    employee_ids: List[int],
    assignment: EmployeeAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Assign multiple employees to a factory/line at once."""
    # Verify factory exists
    factory = db.query(Factory).filter(Factory.id == assignment.factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    updated = []
    not_found = []

    for emp_id in employee_ids:
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            not_found.append(emp_id)
            continue

        employee.factory_id = assignment.factory_id
        employee.factory_line_id = assignment.factory_line_id
        employee.company_name = assignment.company_name or factory.company_name
        employee.plant_name = assignment.plant_name or factory.plant_name
        employee.department = assignment.department
        employee.line_name = assignment.line_name
        employee.position = assignment.position

        if assignment.hourly_rate is not None:
            employee.hourly_rate = assignment.hourly_rate
        if assignment.billing_rate is not None:
            employee.billing_rate = assignment.billing_rate

        updated.append(emp_id)

    db.commit()

    return {
        "updated_count": len(updated),
        "not_found_count": len(not_found),
        "updated_ids": updated,
        "not_found_ids": not_found
    }
