"""
Import API Router - データインポートAPI

Provides endpoints for importing factories and employees from JSON/Excel files.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rate_limit import limiter, RateLimits
from app.services.import_service import ImportService

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================

class PreviewItem(BaseModel):
    """Single item in preview data."""
    row: int
    is_valid: bool
    errors: List[str] = []
    _raw: dict = {}

    class Config:
        extra = "allow"


class ImportRequest(BaseModel):
    """Request to execute import after preview."""
    preview_data: List[dict]
    mode: str = "create"  # create, update, sync


class ImportResponse(BaseModel):
    """Response from import operations."""
    success: bool
    total_rows: int
    imported_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: List[dict] = []
    preview_data: List[dict] = []
    message: str


# ========================================
# FACTORY IMPORT ENDPOINTS
# ========================================

@router.post("/factories/preview", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_PREVIEW)
async def preview_factory_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Preview factory import from JSON or Excel file.

    Upload a file to see what will be imported before confirming.
    Supports:
    - JSON files (.json)
    - Excel files (.xlsx, .xls, .xlsm)

    Returns preview data with validation errors.
    """
    # Validate file type
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.json', '.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="サポートされていないファイル形式です。JSON または Excel ファイルをアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)

    if filename.endswith('.json'):
        result = service.preview_factories_json(content)
    else:
        result = service.preview_factories_excel(content)

    return ImportResponse(**result.to_dict())


@router.post("/factories/execute", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def execute_factory_import(
    request: Request,
    import_data: ImportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Execute factory import after preview confirmation.

    Args:
        preview_data: Data from preview step
        mode: Import mode
            - "create": Only create new records, skip existing
            - "update": Update existing records, create new ones
            - "sync": Full sync (update + create)
    """
    service = ImportService(db)
    result = service.import_factories(import_data.preview_data, import_data.mode)
    return ImportResponse(**result.to_dict())


# ========================================
# EMPLOYEE IMPORT ENDPOINTS
# ========================================

@router.post("/employees/preview", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_PREVIEW)
async def preview_employee_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Preview employee import from Excel file.

    Upload an Excel file (.xlsx, .xlsm) to see what will be imported.

    Expected columns (Japanese or English):
    - 社員№ / employee_number (required)
    - 氏名 / full_name_kanji (required)
    - カナ / full_name_kana (required)
    - 入社日 / hire_date (required)
    - その他オプション項目...

    Returns preview data with validation errors.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)
    result = service.preview_employees_excel(content)

    return ImportResponse(**result.to_dict())


@router.post("/employees/execute", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def execute_employee_import(
    request: Request,
    import_data: ImportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Execute employee import after preview confirmation.

    Args:
        preview_data: Data from preview step
        mode: Import mode
            - "create": Only create new records
            - "update": Only update existing records
            - "sync": Create new + update existing (recommended)
    """
    service = ImportService(db)
    result = service.import_employees(import_data.preview_data, import_data.mode)
    return ImportResponse(**result.to_dict())


@router.post("/employees/sync", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def sync_employees_from_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    One-click sync employees from Excel.

    Combines preview and execute in one step for quick sync.
    - Creates new employees not in database
    - Updates existing employees with new data
    - Does NOT delete employees not in Excel

    Use this for regular sync operations.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)

    # Preview first
    preview_result = service.preview_employees_excel(content)

    # If there are critical errors, return preview result
    if not preview_result.success:
        return ImportResponse(**preview_result.to_dict())

    # Execute sync
    import_result = service.import_employees(preview_result.preview_data, mode="sync")
    return ImportResponse(**import_result.to_dict())


# ========================================
# TEMPLATE DOWNLOAD ENDPOINTS
# ========================================

@router.get("/templates/factories")
async def download_factory_template(
    format: str = Query("excel", description="Template format: excel or json"),
):
    """
    Download a template file for factory import.

    Returns an empty template with the expected columns/structure.
    """
    from fastapi.responses import Response

    if format == "json":
        template = {
            "company_name": "会社名を入力",
            "plant_name": "工場名を入力",
            "plant_address": "工場住所",
            "conflict_date": "2026-12-31",
            "client_responsible_name": "派遣先責任者名",
            "client_complaint_name": "苦情処理担当者名",
            "closing_date": "月末日",
            "payment_date": "翌月末日"
        }
        import json
        content = json.dumps([template], ensure_ascii=False, indent=2)
        return Response(
            content=content.encode('utf-8'),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=factory_template.json"}
        )
    else:
        # Excel template
        import pandas as pd
        from io import BytesIO

        df = pd.DataFrame([{
            "派遣先名": "",
            "工場名": "",
            "工場住所": "",
            "抵触日": "",
            "派遣先責任者": "",
            "派遣先苦情担当者": "",
            "締め日": "",
            "支払日": ""
        }])

        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=factory_template.xlsx"}
        )


@router.get("/templates/employees")
async def download_employee_template():
    """
    Download a template Excel file for employee import.

    Returns an empty template with all expected columns.
    """
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import Response

    df = pd.DataFrame([{
        "社員№": "",
        "氏名": "",
        "カナ": "",
        "ローマ字": "",
        "性別": "",
        "生年月日": "",
        "国籍": "ベトナム",
        "住所": "",
        "電話番号": "",
        "携帯電話": "",
        "入社日": "",
        "退社日": "",
        "派遣先": "",
        "工場": "",
        "配属先": "",
        "ライン": "",
        "時給": "",
        "請求単価": "",
        "在留資格": "",
        "ビザ期限": "",
        "在留カード番号": "",
        "雇用保険": "○",
        "健康保険": "○",
        "厚生年金": "○",
        "備考": ""
    }])

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employee_template.xlsx"}
    )
