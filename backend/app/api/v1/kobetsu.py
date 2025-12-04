"""
Kobetsu Keiyakusho API Router

個別契約書 (Individual Contract) endpoints for managing dispatch contracts
under 労働者派遣法第26条 (Worker Dispatch Law Article 26).

Provides 24 endpoints for full contract lifecycle management.
"""
import csv
import io
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.kobetsu_keiyakusho import KobetsuEmployee
from app.models.employee import Employee
from app.models.factory import Factory, FactoryLine
from app.services.kobetsu_service import KobetsuService
from app.services.kobetsu_pdf_service import KobetsuPDFService
from app.services.contract_logic_service import ContractLogicService, ContractValidationError
from app.services.contract_date_service import ContractDateService
from app.services.contract_renewal_service import ContractRenewalService
from app.services.employee_compatibility_service import EmployeeCompatibilityValidator
from app.schemas.kobetsu_keiyakusho import (
    KobetsuKeiyakushoCreate,
    KobetsuKeiyakushoUpdate,
    KobetsuKeiyakushoResponse,
    KobetsuKeiyakushoList,
    KobetsuKeiyakushoStats,
    RateGroupingRequest,
    RateGroupingResponse,
    RateGroup,
    EmployeeInGroup,
    KobetsuBatchCreateRequest,
    KobetsuBatchCreateResponse,
)
from app.api.v1.helpers import (
    get_contract_or_404,
    get_employee_or_404,
    get_factory_or_404,
    validate_contract_status,
    validate_date_range,
)

router = APIRouter(redirect_slashes=False)


# ========================================
# LIST & SEARCH ENDPOINTS
# ========================================

@router.get("", response_model=dict)
async def list_contracts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    search: Optional[str] = Query(None, description="Search in contract number and worksite"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get paginated list of Kobetsu Keiyakusho contracts.

    Returns list of contracts with pagination metadata.
    Supports filtering by status, factory, date range, and text search.
    """
    service = KobetsuService(db)
    contracts, total = service.get_list(
        skip=skip,
        limit=limit,
        status=status,
        factory_id=factory_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": [KobetsuKeiyakushoList.model_validate(c) for c in contracts],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(contracts) < total,
    }


@router.get("/stats", response_model=KobetsuKeiyakushoStats)
async def get_statistics(
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get contract statistics.

    Returns counts of contracts by status, expiring soon count,
    and total workers in active contracts.
    """
    service = KobetsuService(db)
    return service.get_stats(factory_id=factory_id)


@router.get("/expiring", response_model=List[KobetsuKeiyakushoList])
async def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get contracts expiring within specified days.

    Useful for renewal planning and notifications.
    """
    service = KobetsuService(db)
    contracts = service.get_expiring_contracts(days=days)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


@router.get("/by-factory/{factory_id}", response_model=List[KobetsuKeiyakushoList])
async def get_contracts_by_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all contracts for a specific factory.
    """
    service = KobetsuService(db)
    contracts = service.get_by_factory(factory_id)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


@router.get("/by-employee/{employee_id}", response_model=List[KobetsuKeiyakushoList])
async def get_contracts_by_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all contracts for a specific employee.
    """
    service = KobetsuService(db)
    contracts = service.get_by_employee(employee_id)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


# ========================================
# DELETE ALL ENDPOINT (Must be before /{contract_id})
# ========================================

@router.delete("/delete-all", status_code=status.HTTP_200_OK)
async def delete_all_contracts(
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable in production
):
    """Delete ALL kobetsu keiyakusho contracts from database. WARNING: This is a destructive operation!"""
    try:
        from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, kobetsu_employees

        # Count before deletion
        contract_count = db.query(KobetsuKeiyakusho).count()

        # Delete association table first
        db.execute(kobetsu_employees.delete())

        # Delete all contracts
        db.query(KobetsuKeiyakusho).delete()

        db.commit()

        return {
            "message": f"Successfully deleted all kobetsu contracts",
            "deleted_count": contract_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contracts: {str(e)}"
        )


# ========================================
# CRUD ENDPOINTS
# ========================================

@router.post("", response_model=KobetsuKeiyakushoResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: KobetsuKeiyakushoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new Kobetsu Keiyakusho (個別契約書).

    Creates a contract in 'draft' status with all 16 legally required items
    as defined in 労働者派遣法第26条.

    Required fields include:
    - 業務内容 (work content)
    - 派遣期間 (dispatch period)
    - 就業時間 (work hours)
    - 派遣料金 (dispatch fee)
    - 責任者情報 (manager information)
    - And more...
    """
    service = KobetsuService(db)

    try:
        contract = service.create(data, created_by=current_user.get("id"))
        return KobetsuKeiyakushoResponse.model_validate(contract)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{contract_id}", response_model=KobetsuKeiyakushoResponse)
async def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific contract by ID.

    Returns full contract details including all 16 legally required items.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.get("/by-number/{contract_number}", response_model=KobetsuKeiyakushoResponse)
async def get_contract_by_number(
    contract_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific contract by contract number.

    Contract number format: KOB-YYYYMM-XXXX (e.g., KOB-202411-0001)
    """
    service = KobetsuService(db)
    contract = service.get_by_contract_number(contract_number)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract {contract_number} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.put("/{contract_id}", response_model=KobetsuKeiyakushoResponse)
async def update_contract(
    contract_id: int,
    data: KobetsuKeiyakushoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update an existing contract.

    Only modifiable fields can be updated. Some fields may be
    restricted based on contract status.
    """
    service = KobetsuService(db)
    contract = service.update(contract_id, data)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: int,
    hard: bool = Query(False, description="Permanently delete (only for drafts)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a contract.

    By default, performs soft delete (changes status to 'cancelled').
    Use hard=true to permanently delete (only works for draft contracts).
    """
    service = KobetsuService(db)

    if hard:
        success = service.hard_delete(contract_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot permanently delete: contract not found or not a draft"
            )
    else:
        success = service.delete(contract_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {contract_id} not found"
            )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ========================================
# STATUS MANAGEMENT ENDPOINTS
# ========================================

@router.post("/{contract_id}/activate", response_model=KobetsuKeiyakushoResponse)
async def activate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Activate a draft contract.

    Changes status from 'draft' to 'active'.
    Only draft contracts can be activated.
    """
    service = KobetsuService(db)
    contract = service.activate(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate: contract not found or not a draft"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.post("/{contract_id}/renew", response_model=KobetsuKeiyakushoResponse)
async def renew_contract(
    contract_id: int,
    new_end_date: date = Query(..., description="New dispatch end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Renew a contract with a new end date.

    Creates a new contract based on the original, with:
    - New contract number
    - Start date = original end date + 1 day
    - End date = specified new_end_date
    - Status = 'draft'

    Original contract status is changed to 'renewed'.
    """
    service = KobetsuService(db)
    contract = service.renew(
        contract_id,
        new_end_date=new_end_date,
        created_by=current_user.get("id")
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot renew: contract not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.post("/{contract_id}/duplicate", response_model=KobetsuKeiyakushoResponse)
async def duplicate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a copy of an existing contract.

    Creates a new draft contract with:
    - New contract number
    - Same data as original
    - Status = 'draft'
    """
    service = KobetsuService(db)
    contract = service.duplicate(contract_id, created_by=current_user.get("id"))

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


# ========================================
# EMPLOYEE MANAGEMENT ENDPOINTS
# ========================================

@router.get("/{contract_id}/employees", response_model=List[int])
async def get_contract_employees(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of employee IDs associated with a contract.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return service.get_employees(contract_id)


@router.get("/{contract_id}/employees/details")
async def get_contract_employees_with_rates(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed employee list with effective 単価 for a contract.

    Returns each employee with their effective hourly rate, showing:
    - Employee basic info (社員№, 氏名, カナ)
    - Individual rate (個別単価) if set
    - Effective rate (使用される単価)
    - Rate source (individual/contract/employee)
    - Individual dates (途中入社/退社)
    - Employment type (有期/無期)
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    logic_service = ContractLogicService(db)

    # Get all employees with their individual settings
    kobetsu_employees = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
    ).all()

    result = []
    for ke in kobetsu_employees:
        emp = ke.employee
        effective = logic_service.get_effective_rate(ke, contract)

        result.append({
            "employee_id": emp.id,
            "employee_number": emp.employee_number,
            "full_name_kanji": emp.full_name_kanji,
            "full_name_kana": emp.full_name_kana,
            "nationality": emp.nationality,
            # 単価情報
            "employee_base_rate": float(emp.hourly_rate) if emp.hourly_rate else None,
            "individual_rate": float(ke.hourly_rate) if ke.hourly_rate else None,
            "effective_rate": float(effective["hourly_rate"]) if effective["hourly_rate"] else None,
            "rate_source": effective["source"],
            # 時間外単価
            "overtime_rate": float(effective["overtime_rate"]) if effective["overtime_rate"] else None,
            "night_shift_rate": float(effective["night_shift_rate"]) if effective["night_shift_rate"] else None,
            "holiday_rate": float(effective["holiday_rate"]) if effective["holiday_rate"] else None,
            # 期間
            "individual_start_date": ke.individual_start_date,
            "individual_end_date": ke.individual_end_date,
            "contract_start_date": contract.dispatch_start_date,
            "contract_end_date": contract.dispatch_end_date,
            # 雇用形態
            "is_indefinite_employment": ke.is_indefinite_employment,
            "employment_type_display": "無期雇用" if ke.is_indefinite_employment else "有期雇用",
            # メタデータ
            "notes": ke.notes,
            "created_at": ke.created_at,
        })

    return {
        "contract_id": contract_id,
        "contract_number": contract.contract_number,
        "worksite_name": contract.worksite_name,
        "contract_default_rate": float(contract.hourly_rate),
        "total_employees": len(result),
        "employees": result
    }


@router.post("/{contract_id}/employees/{employee_id}", status_code=status.HTTP_201_CREATED)
async def add_employee_to_contract(
    contract_id: int,
    employee_id: int,
    hourly_rate: Optional[float] = Query(None, description="個別単価 (override)"),
    individual_start_date: Optional[date] = Query(None, description="個別開始日 (途中入社)"),
    individual_end_date: Optional[date] = Query(None, description="個別終了日 (途中退社)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Add an employee to a contract with optional individual rate.

    Parameters:
    - hourly_rate: 個別単価 - Override rate for this employee in this contract
    - individual_start_date: 途中入社 - If employee starts after contract start
    - individual_end_date: 途中退社 - If employee ends before contract end

    If hourly_rate is not provided, uses the employee's base rate.
    """
    logic_service = ContractLogicService(db)

    try:
        kobetsu_employee = logic_service.add_employee_to_contract(
            contract_id=contract_id,
            employee_id=employee_id,
            hourly_rate=Decimal(str(hourly_rate)) if hourly_rate else None,
            individual_start_date=individual_start_date,
            individual_end_date=individual_end_date,
        )
        db.commit()

        return {
            "message": f"Employee {employee_id} added to contract {contract_id}",
            "employee_id": employee_id,
            "contract_id": contract_id,
            "effective_rate": float(kobetsu_employee.hourly_rate) if kobetsu_employee.hourly_rate else None,
            "individual_start_date": kobetsu_employee.individual_start_date,
            "individual_end_date": kobetsu_employee.individual_end_date,
        }

    except ContractValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add employee: {str(e)}"
        )


@router.delete("/{contract_id}/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_employee_from_contract(
    contract_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove an employee from a contract.
    """
    service = KobetsuService(db)
    success = service.remove_employee(contract_id, employee_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove employee: contract or employee not found"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ========================================
# DOCUMENT GENERATION ENDPOINTS
# ========================================

@router.post("/{contract_id}/generate-pdf")
async def generate_contract_pdf(
    contract_id: int,
    format: str = Query("pdf", description="Output format: pdf or docx"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate PDF or DOCX document for a contract.

    Returns the generated document file.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    pdf_service = KobetsuPDFService()

    try:
        if format == "docx":
            file_path = pdf_service.generate_docx(contract)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{contract.contract_number}.docx"
        else:
            file_path = pdf_service.generate_pdf(contract)
            media_type = "application/pdf"
            filename = f"{contract.contract_number}.pdf"

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.post("/{contract_id}/sign")
async def sign_contract(
    contract_id: int,
    pdf_path: str = Query(..., description="Path to signed PDF"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a contract as signed and store the signed PDF path.
    """
    service = KobetsuService(db)
    contract = service.sign_contract(contract_id, pdf_path)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return {
        "message": "Contract signed successfully",
        "signed_date": contract.signed_date,
        "pdf_path": contract.pdf_path,
    }


@router.get("/{contract_id}/download")
async def download_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download the signed PDF for a contract.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    if not contract.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No signed PDF available for this contract"
        )

    return FileResponse(
        path=contract.pdf_path,
        media_type="application/pdf",
        filename=f"{contract.contract_number}_signed.pdf",
    )


# ========================================
# ADMIN ENDPOINTS
# ========================================

@router.post("/update-expired", dependencies=[Depends(require_role("admin"))])
async def update_expired_contracts(
    db: Session = Depends(get_db),
):
    """
    Update status of expired contracts.

    Admin-only endpoint that should be called by a scheduled task.
    Marks all active contracts past their end date as 'expired'.
    """
    service = KobetsuService(db)
    count = service.update_expired_contracts()

    return {
        "message": f"Updated {count} expired contracts",
        "count": count,
    }


# ========================================
# SMART ASSIGNMENT ENDPOINTS
# ========================================

@router.get("/suggest/assignment")
async def suggest_employee_assignment(
    employee_id: int = Query(..., description="Employee ID to assign"),
    factory_id: int = Query(..., description="Factory ID"),
    factory_line_id: Optional[int] = Query(None, description="Factory Line ID"),
    start_date: date = Query(..., description="Employee start date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Suggest how to assign an employee: add to existing contract or create new.

    This endpoint analyzes:
    1. If there's an existing active contract for this factory/line
    2. If employee's rate is compatible with existing contract
    3. If dates align properly

    Returns recommendation:
    - "add_to_existing": Employee can join an existing contract
    - "create_new": A new contract should be created

    Example response:
    {
        "recommendation": "add_to_existing",
        "reason": "既存の契約に追加できます。",
        "existing_contract": {
            "id": 123,
            "contract_number": "KOB-202411-0001",
            "dispatch_end_date": "2025-03-31"
        },
        "employee_rate": 1200,
        "contract_rate": 1200,
        "rate_difference_pct": 0
    }
    """
    logic_service = ContractLogicService(db)

    # Get employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Find existing contract
    existing_contract = logic_service.find_existing_contract(
        factory_id=factory_id,
        factory_line_id=factory_line_id,
        target_date=start_date
    )

    # Determine recommendation
    should_create, reason = logic_service.should_create_new_contract(
        employee=employee,
        factory_id=factory_id,
        factory_line_id=factory_line_id,
        start_date=start_date,
        existing_contract=existing_contract
    )

    result = {
        "recommendation": "create_new" if should_create else "add_to_existing",
        "reason": reason,
        "employee_id": employee_id,
        "employee_name": employee.full_name_kanji,
        "employee_rate": float(employee.hourly_rate) if employee.hourly_rate else None,
    }

    if existing_contract:
        rate_diff = 0
        if employee.hourly_rate and existing_contract.hourly_rate:
            rate_diff = abs(float(employee.hourly_rate) - float(existing_contract.hourly_rate))
            rate_diff_pct = (rate_diff / float(existing_contract.hourly_rate)) * 100
        else:
            rate_diff_pct = 0

        result["existing_contract"] = {
            "id": existing_contract.id,
            "contract_number": existing_contract.contract_number,
            "worksite_name": existing_contract.worksite_name,
            "dispatch_start_date": existing_contract.dispatch_start_date,
            "dispatch_end_date": existing_contract.dispatch_end_date,
            "current_workers": existing_contract.number_of_workers,
            "hourly_rate": float(existing_contract.hourly_rate),
        }
        result["rate_difference_pct"] = round(rate_diff_pct, 2)
    else:
        result["existing_contract"] = None
        result["rate_difference_pct"] = None

    # Add conflict date info
    conflict_info = logic_service.get_conflict_date_info(factory_id)
    result["conflict_date_info"] = conflict_info

    return result


@router.post("/assign-employee")
async def smart_assign_employee(
    employee_id: int = Query(..., description="Employee ID"),
    factory_id: int = Query(..., description="Factory ID"),
    factory_line_id: Optional[int] = Query(None, description="Factory Line ID"),
    start_date: date = Query(..., description="Start date"),
    action: str = Query(..., description="Action: 'add_to_existing' or 'create_new'"),
    existing_contract_id: Optional[int] = Query(None, description="Contract ID (if adding to existing)"),
    hourly_rate: Optional[float] = Query(None, description="Individual rate override"),
    duration_months: int = Query(3, description="Contract duration (if creating new)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Execute employee assignment based on chosen action.

    Actions:
    - "add_to_existing": Add employee to existing contract
    - "create_new": Create new contract and add employee

    For "add_to_existing":
    - existing_contract_id is required
    - Employee is added to the specified contract

    For "create_new":
    - A new contract is created with suggested dates
    - Employee is added as the first worker
    """
    logic_service = ContractLogicService(db)
    service = KobetsuService(db)

    # Get employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Get factory
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    if action == "add_to_existing":
        if not existing_contract_id:
            raise HTTPException(
                status_code=400,
                detail="existing_contract_id is required for 'add_to_existing' action"
            )

        try:
            kobetsu_employee = logic_service.add_employee_to_contract(
                contract_id=existing_contract_id,
                employee_id=employee_id,
                hourly_rate=Decimal(str(hourly_rate)) if hourly_rate else None,
                individual_start_date=start_date,
            )
            db.commit()

            return {
                "action": "added_to_existing",
                "contract_id": existing_contract_id,
                "employee_id": employee_id,
                "effective_rate": float(kobetsu_employee.hourly_rate) if kobetsu_employee.hourly_rate else None,
                "message": f"{employee.full_name_kanji}を既存契約に追加しました"
            }

        except ContractValidationError as e:
            raise HTTPException(status_code=400, detail=e.message)

    elif action == "create_new":
        # Get suggested dates
        dates = logic_service.suggest_contract_dates(
            factory_id=factory_id,
            employee_start_date=start_date,
            preferred_duration_months=duration_months
        )

        if "error" in dates:
            raise HTTPException(status_code=400, detail=dates["error"])

        # Get factory line for job description
        line = None
        if factory_line_id:
            line = db.query(FactoryLine).filter(FactoryLine.id == factory_line_id).first()

        # Create contract data
        contract_data = KobetsuKeiyakushoCreate(
            factory_id=factory_id,
            employee_ids=[employee_id],
            contract_date=date.today(),
            dispatch_start_date=dates["suggested_start"],
            dispatch_end_date=dates["suggested_end"],
            work_content=line.job_description if line else "製造業務",
            responsibility_level=line.responsibility_level if line else "通常業務",
            worksite_name=factory.plant_name,
            worksite_address=factory.plant_address or factory.company_address or "",
            organizational_unit=line.department if line else None,
            supervisor_department=line.supervisor_department if line else "製造部",
            supervisor_position="課長",
            supervisor_name=line.supervisor_name if line else factory.client_responsible_name or "",
            work_days=["月", "火", "水", "木", "金"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            haken_moto_complaint_contact={
                "department": factory.dispatch_complaint_department or "管理部",
                "position": "部長",
                "name": factory.dispatch_complaint_name or "",
                "phone": factory.dispatch_complaint_phone or ""
            },
            haken_saki_complaint_contact={
                "department": factory.client_complaint_department or "総務部",
                "position": "部長",
                "name": factory.client_complaint_name or "",
                "phone": factory.client_complaint_phone or ""
            },
            hourly_rate=float(hourly_rate or employee.hourly_rate or 1200),
            overtime_rate=float((hourly_rate or employee.hourly_rate or 1200) * Decimal("1.25")),
            haken_moto_manager={
                "department": factory.dispatch_responsible_department or "派遣事業部",
                "position": "部長",
                "name": factory.dispatch_responsible_name or "",
                "phone": factory.dispatch_responsible_phone or ""
            },
            haken_saki_manager={
                "department": factory.client_responsible_department or "人事部",
                "position": "部長",
                "name": factory.client_responsible_name or "",
                "phone": factory.client_responsible_phone or ""
            },
        )

        try:
            contract = service.create(contract_data, created_by=current_user.get("id"))
            db.commit()

            return {
                "action": "created_new",
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "employee_id": employee_id,
                "dispatch_start_date": contract.dispatch_start_date,
                "dispatch_end_date": contract.dispatch_end_date,
                "warnings": dates.get("warnings", []),
                "message": f"新規契約 {contract.contract_number} を作成し、{employee.full_name_kanji}を追加しました"
            }

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action}. Must be 'add_to_existing' or 'create_new'"
        )


# ========================================
# 抵触日 VALIDATION ENDPOINTS
# ========================================

@router.get("/validate/conflict-date")
async def validate_conflict_date(
    factory_id: int = Query(..., description="Factory ID"),
    dispatch_end_date: date = Query(..., description="Proposed dispatch end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Validate that proposed dispatch_end_date does not exceed factory's 抵触日.

    Returns:
    - is_valid: Whether the date is valid
    - message: Validation message (error or warning)
    - conflict_date: Factory's 抵触日
    - days_remaining: Days until 抵触日
    """
    logic_service = ContractLogicService(db)

    is_valid, message = logic_service.validate_against_conflict_date(
        factory_id=factory_id,
        dispatch_end_date=dispatch_end_date
    )

    conflict_info = logic_service.get_conflict_date_info(factory_id)

    return {
        "is_valid": is_valid,
        "message": message,
        "conflict_date": conflict_info["conflict_date"],
        "days_remaining": conflict_info["days_remaining"],
        "warning_level": conflict_info["warning_level"],
    }


@router.get("/suggest/dates")
async def suggest_contract_dates(
    factory_id: int = Query(..., description="Factory ID"),
    employee_start_date: date = Query(..., description="Employee's start date"),
    duration_months: int = Query(3, ge=1, le=36, description="Preferred contract duration in months"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Suggest optimal contract dates based on factory's 抵触日 and business rules.

    Returns:
    - suggested_start: Recommended start date
    - suggested_end: Recommended end date (adjusted for 抵触日)
    - max_end: Maximum allowed end date
    - conflict_date: Factory's 抵触日
    - warnings: List of warnings or adjustments made
    """
    logic_service = ContractLogicService(db)

    result = logic_service.suggest_contract_dates(
        factory_id=factory_id,
        employee_start_date=employee_start_date,
        preferred_duration_months=duration_months
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result


@router.get("/alerts/expiring-contracts")
async def get_expiring_contracts_alerts(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get contracts expiring within specified days with urgency levels.

    Returns list of contracts sorted by urgency:
    - critical: 7 days or less
    - warning: more than 7 days
    """
    logic_service = ContractLogicService(db)
    return logic_service.get_expiring_contracts(days=days)


@router.get("/alerts/conflict-dates")
async def get_factories_near_conflict_date(
    days: int = Query(90, ge=1, le=365, description="Days until conflict date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get factories approaching their 抵触日 within specified days.

    Returns list of factories with urgency levels:
    - critical: 30 days or less
    - warning: more than 30 days

    Includes count of active workers at each factory.
    """
    logic_service = ContractLogicService(db)
    return logic_service.get_factories_near_conflict_date(days=days)


# ========================================
# VALIDATION ENDPOINTS
# ========================================

@router.post("/validate/employee-compatibility")
async def validate_employee_compatibility(
    employee_ids: List[int] = Query(..., description="Employee IDs to validate"),
    factory_line_id: Optional[int] = Query(None, description="Factory line ID"),
    hourly_rate: Optional[Decimal] = Query(None, description="Hourly rate (tanka)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Validate that multiple employees can work under the same contract.

    Checks:
    ✅ All employees are active (not resigned)
    ✅ All employees are on the SAME factory_line_id
    ✅ Compatible hourly rates
    ✅ No conflicts with employee status/assignment

    Returns:
    {
        "is_valid": bool,
        "compatible_count": int,
        "incompatible_count": int,
        "compatible": [
            {
                "id": 1,
                "employee_number": "EMP001",
                "full_name_kanji": "山田太郎",
                "line_name": "Manual Assembly",
                "status": "compatible"
            }
        ],
        "incompatible": [
            {
                "id": 3,
                "employee_number": "EMP003",
                "full_name_kanji": "神田太郎",
                "line_name": "Welding",
                "issues": [
                    {
                        "type": "different_line",
                        "reason": "Employee is on Welding, contract is for Manual Assembly",
                        "severity": "error"
                    }
                ]
            }
        ],
        "suggestions": [
            "Create separate contract for EMP003 (different line)"
        ],
        "summary": "1 compatible + 1 incompatible → Needs 1 separate contract"
    }

    Example:
        POST /api/v1/kobetsu/validate/employee-compatibility?employee_ids=1&employee_ids=2&employee_ids=3&factory_line_id=5&hourly_rate=1200
    """
    try:
        validator = EmployeeCompatibilityValidator(db)

        # Convert Decimal to proper type if provided
        rate = Decimal(str(hourly_rate)) if hourly_rate else None

        # Validate employees using the service
        result = validator.validate_employees(
            employee_ids=employee_ids,
            factory_line_id=factory_line_id,
            hourly_rate=rate
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# ========================================
# RATE GROUPING ENDPOINTS - 単価別グループ化
# ========================================

@router.post("/group-by-rate", response_model=RateGroupingResponse)
async def group_employees_by_rate(
    request: RateGroupingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Group employees by their hourly rate (単価) for creating separate contracts.

    Use this endpoint when you want to create multiple contracts from a selection
    of employees, where each contract groups employees with the same hourly rate.

    Example:
        Input: employee_ids = [1, 2, 3, 4, 5]
        - Employee 1, 2, 3 have hourly_rate = 1600
        - Employee 4, 5 have hourly_rate = 1650

        Output:
        {
            "total_employees": 5,
            "groups": [
                { "hourly_rate": 1650, "employee_count": 2, "employees": [...] },
                { "hourly_rate": 1600, "employee_count": 3, "employees": [...] }
            ],
            "has_multiple_rates": true,
            "suggested_contracts": 2,
            "message": "5名を2つの契約に分割することを推奨します"
        }
    """
    try:
        # Fetch all requested employees
        employees = db.query(Employee).filter(
            Employee.id.in_(request.employee_ids)
        ).all()

        if not employees:
            raise HTTPException(
                status_code=404,
                detail="指定された従業員が見つかりません"
            )

        # Check for missing IDs
        found_ids = {e.id for e in employees}
        missing_ids = set(request.employee_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"従業員ID {missing_ids} が見つかりません"
            )

        # Group by hourly_rate
        from collections import defaultdict
        rate_groups = defaultdict(list)

        for emp in employees:
            # Use 0 for employees without hourly_rate
            rate = emp.hourly_rate if emp.hourly_rate is not None else Decimal("0")
            rate_groups[rate].append(emp)

        # Build response groups (sorted by rate descending)
        groups = []
        for rate in sorted(rate_groups.keys(), reverse=True):
            emp_list = rate_groups[rate]
            # Get billing_rate from first employee (assume same for group)
            billing_rate = emp_list[0].billing_rate if emp_list else None

            group = RateGroup(
                hourly_rate=rate,
                billing_rate=billing_rate,
                employee_count=len(emp_list),
                employees=[
                    EmployeeInGroup(
                        id=e.id,
                        employee_number=e.employee_number,
                        full_name_kana=e.full_name_kana,
                        full_name_kanji=e.full_name_kanji,
                        hourly_rate=e.hourly_rate,
                        billing_rate=e.billing_rate,
                        department=e.department,
                        line_name=e.line_name,
                        factory_line_id=e.factory_line_id,
                    )
                    for e in sorted(emp_list, key=lambda x: x.employee_number)
                ]
            )
            groups.append(group)

        has_multiple = len(groups) > 1
        suggested = len(groups)

        if has_multiple:
            message = f"{len(employees)}名を{suggested}つの契約に分割することを推奨します"
        else:
            rate = groups[0].hourly_rate if groups else 0
            message = f"{len(employees)}名全員が同じ単価（¥{rate:,.0f}）です"

        return RateGroupingResponse(
            total_employees=len(employees),
            groups=groups,
            has_multiple_rates=has_multiple,
            suggested_contracts=suggested,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"グループ化処理でエラーが発生しました: {str(e)}"
        )


@router.post("/batch-create", response_model=KobetsuBatchCreateResponse)
async def batch_create_contracts(
    request: KobetsuBatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create multiple contracts in batch, one for each rate group.

    This endpoint allows creating multiple 個別契約書 at once, where each
    contract has employees with the same hourly rate.

    Example:
        Create 2 contracts from 5 employees:
        - Contract 1: employees [1,2,3] with hourly_rate=1600
        - Contract 2: employees [4,5] with hourly_rate=1650

    All contracts share the same:
        - Factory, work location, dates
        - Work content, supervisor info
        - Schedule (days, times, break)

    Each contract has its own:
        - Employee list
        - Hourly rate (and billing rate)
        - Number of workers (auto-calculated)
        - Contract number (auto-generated)
    """
    try:
        service = KobetsuService(db)
        created_contracts = []

        for idx, contract_item in enumerate(request.contracts):
            # Calculate number of workers if not provided
            num_workers = contract_item.number_of_workers or len(contract_item.employee_ids)

            # Build create data for this contract
            # We need to create a KobetsuKeiyakushoCreate-compatible dict
            contract_data = KobetsuKeiyakushoCreate(
                factory_id=request.factory_id,
                employee_ids=contract_item.employee_ids,
                contract_date=request.contract_date,
                dispatch_start_date=request.dispatch_start_date,
                dispatch_end_date=request.dispatch_end_date,
                work_content=request.work_content,
                responsibility_level=request.responsibility_level,
                worksite_name=request.worksite_name,
                worksite_address=request.worksite_address,
                supervisor_department=request.supervisor_department,
                supervisor_position=request.supervisor_position,
                supervisor_name=request.supervisor_name,
                supervisor_phone=request.supervisor_phone,
                work_days=request.work_days,
                work_start_time=request.work_start_time,
                work_end_time=request.work_end_time,
                break_time_minutes=request.break_time_minutes,
                hourly_rate=contract_item.hourly_rate,
                overtime_rate=contract_item.hourly_rate * Decimal("1.25"),  # Default overtime
            )

            # Create the contract
            contract = service.create(contract_data)

            created_contracts.append({
                "id": contract.id,
                "contract_number": contract.contract_number,
                "hourly_rate": float(contract_item.hourly_rate),
                "number_of_workers": num_workers,
                "employee_ids": contract_item.employee_ids,
            })

        db.commit()

        return KobetsuBatchCreateResponse(
            success=True,
            created_count=len(created_contracts),
            contracts=created_contracts,
            message=f"{len(created_contracts)}件の契約を作成しました",
        )

    except ContractValidationError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"一括作成でエラーが発生しました: {str(e)}"
        )


# ========================================
# RENEWAL ENDPOINTS - Contract cycle management
# ========================================

@router.get("/{kobetsu_id}/renewal-info")
async def get_renewal_info(
    kobetsu_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get preview information about what will be renewed for a contract.

    Shows:
    - Current contract details
    - Calculated new contract dates based on factory cycle
    - Employee status
    - Number of fields that will be copied
    - Any warnings (e.g., resigned employees)

    Useful for showing a preview before renewal.
    """
    try:
        renewal_service = ContractRenewalService(db)
        info = renewal_service.get_renewal_info(kobetsu_id)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{kobetsu_id}/renew")
async def renew_contract(
    kobetsu_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate next contract based on factory cycle configuration.

    This endpoint:
    1. Retrieves the current contract
    2. Validates all employees are still active
    3. Calculates new contract dates based on factory cycle rules
    4. Creates a new contract with status='draft'
    5. Links to previous contract for audit trail

    The new contract copies:
    - Work location, content, responsibility level
    - Work schedule (days, hours, breaks)
    - Supervisor information
    - Contact and manager information
    - Payment rates (can be edited before activation)

    The new contract does NOT copy:
    - contract_number (auto-generated)
    - status (set to 'draft')
    - created_at (set to now)
    - pdf_path (reset)
    - signatures/approvals

    Returns:
        New KobetsuKeiyakusho contract with status='draft'

    Raises:
        404: Contract not found
        400: Employee validation failed (resigned employees)
        422: Factory cycle configuration invalid

    Example:
        POST /api/v1/kobetsu/42/renew

        Response:
        {
          "id": 43,
          "contract_number": "KOB-202412-0001",
          "dispatch_start_date": "2025-05-01",
          "dispatch_end_date": "2025-05-31",
          "status": "draft",
          "previous_contract_id": 42,
          ...other fields...
        }
    """
    try:
        renewal_service = ContractRenewalService(db)
        renewed_contract = renewal_service.renew_contract(
            current_contract_id=kobetsu_id,
            created_by_id=current_user.get('id')
        )
        return KobetsuKeiyakushoResponse.model_validate(renewed_contract)
    except ValueError as e:
        # Employee validation or contract not found
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Renewal failed: {str(e)}")


@router.get("/{factory_id}/cycle-info")
async def get_factory_cycle_info(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get factory contract cycle information.

    Returns:
    - Cycle type (monthly or annual)
    - Fiscal year end date
    - Human-readable description
    - Example of calculated dates if contract starts today

    Useful for frontend to show cycle rules and auto-calculate contract dates.

    Example response:
    {
      "factory_id": 1,
      "cycle_type": "monthly",
      "fiscal_year_end": "4/30",
      "description": "月次契約 (毎月更新)",
      "example": {
        "if_start_today": "2024-11-30",
        "calculated_end": "2024-12-31"
      }
    }
    """
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    date_service = ContractDateService(db)

    # Calculate example dates
    today = date.today()
    start_date, end_date = date_service.calculate_contract_dates(
        factory_id=factory_id,
        employee_start_date=today
    )

    return {
        "factory_id": factory_id,
        "cycle_type": factory.contract_cycle_type.value,
        "cycle_day_type": factory.cycle_day_type.value,
        "fiscal_year_end": f"{factory.fiscal_year_end_month}/{factory.fiscal_year_end_day}",
        "description": date_service.get_cycle_description(factory_id),
        "example": {
            "if_start_today": str(today),
            "calculated_end": str(end_date),
            "duration_days": (end_date - start_date).days + 1
        }
    }


# ========================================
# EXPORT ENDPOINTS
# ========================================

@router.get("/export/csv")
async def export_contracts_csv(
    status: Optional[str] = Query(None, description="Filter by status"),
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Export contracts to CSV format.
    """
    service = KobetsuService(db)
    contracts, _ = service.get_list(
        skip=0,
        limit=10000,  # Max export
        status=status,
        factory_id=factory_id,
    )

    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "契約番号", "派遣先名", "開始日", "終了日", "労働者数", "ステータス", "作成日"
    ])

    # Data rows
    for c in contracts:
        writer.writerow([
            c.contract_number,
            c.worksite_name,
            c.dispatch_start_date.isoformat(),
            c.dispatch_end_date.isoformat(),
            c.number_of_workers,
            c.status,
            c.created_at.isoformat(),
        ])

    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=kobetsu_contracts.csv"
        }
    )
