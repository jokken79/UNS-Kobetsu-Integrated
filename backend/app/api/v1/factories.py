"""
Factory API Router - 派遣先/工場 endpoints.

Provides CRUD operations and cascade dropdown support for:
派遣先 → 工場名 → 配属先 → ライン
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, distinct

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee
from app.schemas.factory import (
    FactoryCreate, FactoryUpdate, FactoryResponse, FactoryListItem,
    FactoryLineCreate, FactoryLineUpdate, FactoryLineResponse,
    CompanyOption, PlantOption, DepartmentOption, LineOption,
    FactoryCascadeData, FactoryJSONImport
)

router = APIRouter(redirect_slashes=False)


# ========================================
# FACTORY CRUD
# ========================================

@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_factory_stats(
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable in production
):
    """Get factory statistics."""
    total_factories = db.query(func.count(Factory.id)).scalar()
    active_factories = db.query(func.count(Factory.id)).filter(Factory.is_active == True).scalar()
    total_lines = db.query(func.count(FactoryLine.id)).scalar()
    active_lines = db.query(func.count(FactoryLine.id)).filter(FactoryLine.is_active == True).scalar()

    return {
        "total_factories": total_factories,
        "active_factories": active_factories,
        "total_lines": total_lines,
        "active_lines": active_lines
    }


@router.get("", response_model=List[FactoryListItem])
async def list_factories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    company_name: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Get list of factories with optional filters."""
    query = db.query(Factory)

    if is_active is not None:
        query = query.filter(Factory.is_active == is_active)

    if company_name:
        query = query.filter(Factory.company_name == company_name)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Factory.company_name.ilike(search_term)) |
            (Factory.plant_name.ilike(search_term)) |
            (Factory.factory_id.ilike(search_term))
        )

    factories = query.order_by(Factory.company_name, Factory.plant_name).offset(skip).limit(limit).all()

    result = []
    for factory in factories:
        lines_count = db.query(func.count(FactoryLine.id)).filter(
            FactoryLine.factory_id == factory.id,
            FactoryLine.is_active == True
        ).scalar()

        employees_count = db.query(func.count(Employee.id)).filter(
            Employee.factory_id == factory.id,
            Employee.status == "active"
        ).scalar()

        result.append(FactoryListItem(
            id=factory.id,
            factory_id=factory.factory_id,
            company_name=factory.company_name,
            plant_name=factory.plant_name,
            conflict_date=factory.conflict_date,
            is_active=factory.is_active,
            lines_count=lines_count,
            employees_count=employees_count
        ))

    return result


# ========================================
# DELETE ALL ENDPOINT (Must be before /{factory_id})
# ========================================

@router.delete("/delete-all", status_code=status.HTTP_200_OK)
async def delete_all_factories(
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable in production
):
    """Delete ALL factories and factory lines from database. WARNING: This is a destructive operation!"""
    try:
        # Count before deletion
        factory_count = db.query(Factory).count()
        line_count = db.query(FactoryLine).count()

        # First, unlink employees from factories and lines
        employees_updated = db.query(Employee).filter(
            (Employee.factory_id.isnot(None)) | (Employee.factory_line_id.isnot(None))
        ).update({
            'factory_id': None,
            'factory_line_id': None,
            'company_name': None,
            'plant_name': None,
            'department': None,
            'line_name': None
        }, synchronize_session=False)

        # Delete all factory lines (now safe)
        db.query(FactoryLine).delete()

        # Delete all factories
        db.query(Factory).delete()

        db.commit()

        return {
            "message": f"Successfully deleted all factories and lines",
            "deleted_count": factory_count,
            "deleted_lines": line_count,
            "employees_unlinked": employees_updated
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete factories: {str(e)}"
        )


@router.get("/{factory_id}", response_model=FactoryResponse)
async def get_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Get factory details by ID."""
    factory = db.query(Factory).options(
        joinedload(Factory.lines)
    ).filter(Factory.id == factory_id).first()

    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    # Count employees
    employees_count = db.query(func.count(Employee.id)).filter(
        Employee.factory_id == factory.id,
        Employee.status == "active"
    ).scalar()

    response = FactoryResponse.model_validate(factory)
    response.employees_count = employees_count
    return response


@router.post("/", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
async def create_factory(
    factory_data: FactoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new factory."""
    # Generate factory_id if not provided
    if not factory_data.factory_id:
        factory_data.factory_id = f"{factory_data.company_name}__{factory_data.plant_name}"

    # Check for duplicate
    existing = db.query(Factory).filter(
        Factory.factory_id == factory_data.factory_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Factory with ID '{factory_data.factory_id}' already exists"
        )

    # Create factory
    lines_data = factory_data.lines or []
    factory_dict = factory_data.model_dump(exclude={"lines"})
    factory = Factory(**factory_dict)
    db.add(factory)
    db.flush()

    # Create lines
    for line_data in lines_data:
        line = FactoryLine(factory_id=factory.id, **line_data.model_dump())
        db.add(line)

    db.commit()
    db.refresh(factory)

    return FactoryResponse.model_validate(factory)


@router.put("/{factory_id}", response_model=FactoryResponse)
async def update_factory(
    factory_id: int,
    factory_data: FactoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a factory."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()

    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    update_data = factory_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(factory, field, value)

    db.commit()
    db.refresh(factory)

    return FactoryResponse.model_validate(factory)


@router.delete("/{factory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a factory (soft delete by setting is_active=False)."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()

    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    factory.is_active = False
    db.commit()


# ========================================
# FACTORY LINE CRUD
# ========================================

@router.get("/{factory_id}/lines", response_model=List[FactoryLineResponse])
async def list_factory_lines(
    factory_id: int,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Get all lines for a factory."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    query = db.query(FactoryLine).filter(FactoryLine.factory_id == factory_id)

    if is_active is not None:
        query = query.filter(FactoryLine.is_active == is_active)

    return query.order_by(FactoryLine.display_order, FactoryLine.department).all()


@router.post("/{factory_id}/lines", response_model=FactoryLineResponse, status_code=status.HTTP_201_CREATED)
async def create_factory_line(
    factory_id: int,
    line_data: FactoryLineCreate,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Create a new line for a factory."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    line = FactoryLine(factory_id=factory_id, **line_data.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)

    return line


@router.put("/lines/{line_id}", response_model=FactoryLineResponse)
async def update_factory_line(
    line_id: int,
    line_data: FactoryLineUpdate,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Update a factory line."""
    line = db.query(FactoryLine).filter(FactoryLine.id == line_id).first()

    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    update_data = line_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(line, field, value)

    db.commit()
    db.refresh(line)

    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_factory_line(
    line_id: int,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # TODO: Re-enable auth in production
):
    """Delete a factory line (soft delete)."""
    line = db.query(FactoryLine).filter(FactoryLine.id == line_id).first()

    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    line.is_active = False
    db.commit()


# ========================================
# CASCADE DROPDOWN ENDPOINTS
# ========================================

@router.get("/dropdown/companies", response_model=List[CompanyOption])
async def get_company_options(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Step 1: Get unique company names for 派遣先 dropdown.
    """
    query = db.query(
        Factory.company_name,
        func.count(Factory.id).label('factories_count')
    ).filter(Factory.is_active == True)

    if search:
        query = query.filter(Factory.company_name.ilike(f"%{search}%"))

    results = query.group_by(Factory.company_name).order_by(Factory.company_name).all()

    return [
        CompanyOption(company_name=r.company_name, factories_count=r.factories_count)
        for r in results
    ]


@router.get("/dropdown/plants", response_model=List[PlantOption])
async def get_plant_options(
    company_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Step 2: Get plants/factories for a selected company (工場名 dropdown).
    """
    factories = db.query(Factory).filter(
        Factory.company_name == company_name,
        Factory.is_active == True
    ).order_by(Factory.plant_name).all()

    return [
        PlantOption(
            id=f.id,
            factory_id=f.factory_id,
            plant_name=f.plant_name,
            plant_address=f.plant_address
        )
        for f in factories
    ]


@router.get("/dropdown/departments", response_model=List[DepartmentOption])
async def get_department_options(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Step 3: Get departments for a selected factory (配属先 dropdown).
    """
    results = db.query(
        FactoryLine.department,
        func.count(FactoryLine.id).label('lines_count')
    ).filter(
        FactoryLine.factory_id == factory_id,
        FactoryLine.is_active == True,
        FactoryLine.department.isnot(None)
    ).group_by(FactoryLine.department).order_by(FactoryLine.department).all()

    return [
        DepartmentOption(department=r.department or "未設定", lines_count=r.lines_count)
        for r in results
    ]


@router.get("/dropdown/lines", response_model=List[LineOption])
async def get_line_options(
    factory_id: int,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Step 4: Get lines for a selected factory/department (ライン dropdown).
    """
    query = db.query(FactoryLine).filter(
        FactoryLine.factory_id == factory_id,
        FactoryLine.is_active == True
    )

    if department:
        query = query.filter(FactoryLine.department == department)

    lines = query.order_by(FactoryLine.display_order, FactoryLine.line_name).all()

    return [
        LineOption(
            id=line.id,
            line_id=line.line_id,
            line_name=line.line_name or "デフォルト",
            job_description=line.job_description,
            hourly_rate=line.hourly_rate,
            supervisor_name=line.supervisor_name
        )
        for line in lines
    ]


@router.get("/dropdown/cascade/{line_id}", response_model=FactoryCascadeData)
async def get_cascade_data(
    line_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete factory and line data for a selected line.
    Used to populate form fields after cascade selection.
    """
    line = db.query(FactoryLine).options(
        joinedload(FactoryLine.factory)
    ).filter(FactoryLine.id == line_id).first()

    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    return FactoryCascadeData(
        factory=FactoryResponse.model_validate(line.factory),
        line=FactoryLineResponse.model_validate(line)
    )


# ========================================
# IMPORT ENDPOINT
# ========================================

@router.post("/import", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
async def import_factory_from_json(
    import_data: FactoryJSONImport,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Import a factory from JSON structure (matches UNS-ClaudeJP-6.0.0 format).
    """
    # Check for existing
    existing = db.query(Factory).filter(
        Factory.factory_id == import_data.factory_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Factory '{import_data.factory_id}' already exists"
        )

    # Map JSON structure to model
    client = import_data.client_company
    plant = import_data.plant
    dispatch = import_data.dispatch_company
    schedule = import_data.schedule
    payment = import_data.payment
    agreement = import_data.agreement

    factory = Factory(
        factory_id=import_data.factory_id,
        # Client company
        company_name=client.get("name", ""),
        company_address=client.get("address"),
        company_phone=client.get("phone"),
        company_fax=client.get("fax"),
        client_responsible_department=client.get("responsible", {}).get("department"),
        client_responsible_name=client.get("responsible", {}).get("name"),
        client_responsible_phone=client.get("responsible", {}).get("phone"),
        client_complaint_department=client.get("complaint", {}).get("department"),
        client_complaint_name=client.get("complaint", {}).get("name"),
        client_complaint_phone=client.get("complaint", {}).get("phone"),
        # Plant
        plant_name=plant.get("name", ""),
        plant_address=plant.get("address"),
        plant_phone=plant.get("phone"),
        # Dispatch company
        dispatch_responsible_department=dispatch.get("responsible", {}).get("department"),
        dispatch_responsible_name=dispatch.get("responsible", {}).get("name"),
        dispatch_responsible_phone=dispatch.get("responsible", {}).get("phone"),
        dispatch_complaint_department=dispatch.get("complaint", {}).get("department"),
        dispatch_complaint_name=dispatch.get("complaint", {}).get("name"),
        dispatch_complaint_phone=dispatch.get("complaint", {}).get("phone"),
        # Schedule
        work_hours_description=schedule.get("work_hours"),
        break_time_description=schedule.get("break_time"),
        calendar_description=schedule.get("calendar"),
        overtime_description=schedule.get("overtime", {}).get("description"),
        holiday_work_description=schedule.get("holiday_work", {}).get("description"),
        conflict_date=schedule.get("conflict_date"),
        # Payment
        closing_date=payment.get("closing_date"),
        payment_date=payment.get("payment_date"),
        bank_account=payment.get("bank_account"),
        # Agreement
        agreement_period=agreement.get("period"),
    )

    db.add(factory)
    db.flush()

    # Import lines
    for line_data in import_data.lines:
        line = FactoryLine(
            factory_id=factory.id,
            line_id=line_data.get("line_id"),
            department=line_data.get("department"),
            line_name=line_data.get("line_name"),
            supervisor_department=line_data.get("supervisor", {}).get("department"),
            supervisor_name=line_data.get("supervisor", {}).get("name"),
            supervisor_phone=line_data.get("supervisor", {}).get("phone"),
            job_description=line_data.get("job_description"),
            job_description_detail=line_data.get("job_description_detail"),
            responsibility_level=line_data.get("responsibility_level", "通常業務"),
            hourly_rate=line_data.get("hourly_rate"),
            billing_rate=line_data.get("billing_rate"),
        )
        db.add(line)

    db.commit()
    db.refresh(factory)

    return FactoryResponse.model_validate(factory)


@router.post("/import/bulk", status_code=status.HTTP_201_CREATED)
async def import_factories_bulk(
    factories: List[FactoryJSONImport],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Bulk import factories from JSON array.
    Returns summary of imported/skipped factories.
    """
    imported = []
    skipped = []

    for factory_data in factories:
        existing = db.query(Factory).filter(
            Factory.factory_id == factory_data.factory_id
        ).first()

        if existing:
            skipped.append(factory_data.factory_id)
            continue

        try:
            client = factory_data.client_company
            plant = factory_data.plant
            dispatch = factory_data.dispatch_company
            schedule = factory_data.schedule
            payment = factory_data.payment
            agreement = factory_data.agreement

            factory = Factory(
                factory_id=factory_data.factory_id,
                company_name=client.get("name", ""),
                company_address=client.get("address"),
                plant_name=plant.get("name", ""),
                plant_address=plant.get("address"),
                conflict_date=schedule.get("conflict_date"),
            )
            db.add(factory)
            db.flush()

            for line_data in factory_data.lines:
                line = FactoryLine(
                    factory_id=factory.id,
                    line_id=line_data.get("line_id"),
                    department=line_data.get("department"),
                    line_name=line_data.get("line_name"),
                    job_description=line_data.get("job_description"),
                    hourly_rate=line_data.get("hourly_rate"),
                )
                db.add(line)

            imported.append(factory_data.factory_id)

        except Exception as e:
            skipped.append(f"{factory_data.factory_id}: {str(e)}")

    db.commit()

    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped
    }
