"""
Document Generation API - 書類生成API

Endpoints for generating dispatch-related documents:
1. 個別契約書 (Individual Contract)
2. 就業条件明示書 (Working Conditions)
3. 派遣通知書 (Dispatch Notification)
4. 派遣先管理台帳 (Destination Ledger)
5. 派遣元管理台帳 (Source Ledger)
6. 派遣時の待遇情報明示書 (Treatment Info at Dispatch) - NEW
7. 雇入れ時の待遇情報明示書 (Treatment Info at Hiring) - NEW
8. 就業状況報告書 (Employment Status Report) - NEW
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.dispatch_documents_service import DispatchDocumentService
from app.services.treatment_document_service import TreatmentDocumentService
from app.services.employment_status_report_service import EmploymentStatusReportService
from app.services.excel_document_service import ExcelDocumentService
from app.services.excel_xml_service import ExcelXMLService
from app.services.kobetsu_excel_generator import KobetsuExcelGenerator
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.employee import Employee
from app.models.factory import Factory
from app.utils.pdf_converter import convert_docx_to_pdf, PDFConversionError
from app.core.config import settings
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ========================================
# File storage helpers
# ========================================

def _save_document(content: bytes, filename: str, subfolder: str = "") -> str:
    """
    Save document to the outputs directory.

    Args:
        content: Document bytes (DOCX or PDF)
        filename: Full filename with extension
        subfolder: Optional subfolder (e.g., 'treatment', 'reports')

    Returns:
        str: Path to saved file
    """
    output_dir = Path(settings.PDF_OUTPUT_DIR)
    if subfolder:
        output_dir = output_dir / subfolder
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / filename
    file_path.write_bytes(content)
    logger.info(f"Document saved: {file_path}")
    return str(file_path)


# ========================================
# Response helpers
# ========================================

def _document_response(
    doc_bytes: bytes,
    filename: str,
    output_format: str = "docx",
    save_copy: bool = True,
    subfolder: str = ""
) -> Response:
    """
    Create appropriate Response based on requested format.
    Optionally saves a copy to disk.

    Args:
        doc_bytes: DOCX document bytes
        filename: Base filename (without extension)
        output_format: 'docx' or 'pdf'
        save_copy: Whether to save a copy to disk (default: True)
        subfolder: Subfolder for saving (e.g., 'treatment', 'reports')

    Returns:
        FastAPI Response with correct content type
    """
    from urllib.parse import quote

    # RFC 5987 encoding for non-ASCII filenames
    def get_content_disposition(fname: str) -> str:
        # URL-encode for filename* parameter (UTF-8)
        encoded = quote(fname, safe='')
        return f"attachment; filename*=UTF-8''{encoded}"

    if output_format.lower() == "pdf":
        try:
            pdf_bytes = convert_docx_to_pdf(doc_bytes)
            full_filename = f"{filename}.pdf"

            # Save copy to disk
            if save_copy:
                _save_document(pdf_bytes, full_filename, subfolder)

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": get_content_disposition(full_filename)
                }
            )
        except PDFConversionError as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF conversion failed: {str(e)}. Try format=docx instead."
            )
    else:
        full_filename = f"{filename}.docx"

        # Save copy to disk
        if save_copy:
            _save_document(doc_bytes, full_filename, subfolder)

        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": get_content_disposition(full_filename)
            }
        )


# ========================================
# Generate documents from contract ID
# ========================================

@router.get("/{contract_id}/kobetsu-keiyakusho")
async def generate_kobetsu_keiyakusho(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 個別契約書 (Individual Contract) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Build data dict from contract
    data = _build_contract_data(contract)

    service = DispatchDocumentService()
    doc_bytes = service.generate_kobetsu_keiyakusho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=kobetsu_keiyakusho_{contract.contract_number}.docx"
        }
    )


@router.get("/{contract_id}/jinzai-haken-kobetsu")
async def generate_jinzai_haken_kobetsu_keiyakusho(
    contract_id: int,
    format: str = Query("docx", description="Output format: 'docx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 人材派遣個別契約書 - EXACT PDF clone format.
    This is the compact 1-page A4 document matching the reference PDF layout.

    Query params:
    - format: Output format ('docx' or 'pdf')
    """
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    factory = contract.factory

    # Build data dict with all fields for the exact PDF clone
    data = _build_jinzai_haken_data(contract, factory)

    service = DispatchDocumentService()
    doc_bytes = service.generate_jinzai_haken_kobetsu_keiyakusho(data)

    # Filename with factory name
    factory_name = (factory.plant_name or factory.company_name if factory else "").replace(" ", "_")
    filename = f"人材派遣個別契約書_{factory_name}_{contract.contract_number}"
    return _document_response(doc_bytes, filename, format, subfolder="contracts")


@router.get("/{contract_id}/shugyo-joken")
async def generate_shugyo_joken_meijisho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 就業条件明示書 (Working Conditions) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_worker_condition_data(contract, kobetsu_emp, employee)

    service = DispatchDocumentService()
    doc_bytes = service.generate_shugyo_joken_meijisho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=shugyo_joken_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/haken-tsuchisho")
async def generate_haken_tsuchisho(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣通知書 (Dispatch Notification) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get all employees for this contract
    kobetsu_employees = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
    ).all()

    if not kobetsu_employees:
        raise HTTPException(status_code=404, detail="No employees assigned to this contract")

    data = _build_notification_data(contract, kobetsu_employees)

    service = DispatchDocumentService()
    doc_bytes = service.generate_haken_tsuchisho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=haken_tsuchisho_{contract.contract_number}.docx"
        }
    )


@router.get("/{contract_id}/hakensaki-daicho")
async def generate_hakensaki_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣先管理台帳 (Destination Ledger) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_ledger_data(contract, kobetsu_emp, employee, is_source=False)

    service = DispatchDocumentService()
    doc_bytes = service.generate_hakensaki_kanri_daicho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=hakensaki_daicho_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/hakenmoto-daicho")
async def generate_hakenmoto_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣元管理台帳 (Source Ledger) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_ledger_data(contract, kobetsu_emp, employee, is_source=True)

    service = DispatchDocumentService()
    doc_bytes = service.generate_hakenmoto_kanri_daicho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=hakenmoto_daicho_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/kobetsu-shugyo-combined")
async def generate_kobetsu_shugyo_combined(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate combined 個別契約書 + 就業条件明示書 on ONE A4 page.

    This is the compact format that combines both documents for efficiency.
    派遣元 ↔ 派遣先 契約 + 派遣労働者への条件明示
    """
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee

    # Build combined data from contract and worker
    data = _build_combined_data(contract, kobetsu_emp, employee)

    service = DispatchDocumentService()
    doc_bytes = service.generate_kobetsu_shugyo_combined(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=kobetsu_shugyo_{contract.contract_number}_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/all-documents")
async def generate_all_documents(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate all documents for a contract as a ZIP file.

    Includes:
    - 個別契約書
    - 就業条件明示書 (for each employee)
    - 派遣通知書
    - 派遣先管理台帳 (for each employee)
    - 派遣元管理台帳 (for each employee)
    """
    import zipfile
    from io import BytesIO

    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get employees
    if employee_id:
        kobetsu_employees = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).all()
    else:
        kobetsu_employees = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).all()

    if not kobetsu_employees:
        raise HTTPException(status_code=404, detail="No employees assigned to this contract")

    service = DispatchDocumentService()

    # Create ZIP file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 個別契約書
        data = _build_contract_data(contract)
        doc_bytes = service.generate_kobetsu_keiyakusho(data)
        zip_file.writestr(f"01_個別契約書_{contract.contract_number}.docx", doc_bytes)

        # 2. 派遣通知書
        notif_data = _build_notification_data(contract, kobetsu_employees)
        doc_bytes = service.generate_haken_tsuchisho(notif_data)
        zip_file.writestr(f"02_派遣通知書_{contract.contract_number}.docx", doc_bytes)

        # For each employee
        for ke in kobetsu_employees:
            emp = ke.employee
            emp_num = emp.employee_number

            # 3. 就業条件明示書
            worker_data = _build_worker_condition_data(contract, ke, emp)
            doc_bytes = service.generate_shugyo_joken_meijisho(worker_data)
            zip_file.writestr(f"03_就業条件明示書_{emp_num}.docx", doc_bytes)

            # 4. 派遣先管理台帳
            ledger_data = _build_ledger_data(contract, ke, emp, is_source=False)
            doc_bytes = service.generate_hakensaki_kanri_daicho(ledger_data)
            zip_file.writestr(f"04_派遣先管理台帳_{emp_num}.docx", doc_bytes)

            # 5. 派遣元管理台帳
            ledger_data = _build_ledger_data(contract, ke, emp, is_source=True)
            doc_bytes = service.generate_hakenmoto_kanri_daicho(ledger_data)
            zip_file.writestr(f"05_派遣元管理台帳_{emp_num}.docx", doc_bytes)

    zip_buffer.seek(0)

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=documents_{contract.contract_number}.zip"
        }
    )


# ========================================
# NEW: Treatment Information Documents (待遇情報明示書)
# ========================================

@router.get("/{contract_id}/haken-ji-taigu")
async def generate_haken_ji_taigu_meijisho(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("docx", description="Output format: 'docx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 派遣時の待遇情報明示書 (Treatment Info at Dispatch).
    法第31条の2第3項の明示
    派遣元 → 派遣労働者 (when dispatching to a new assignment)

    Query params:
    - employee_id: Optional specific employee ID
    - format: Output format ('docx' or 'pdf')
    """
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee

    # Build data for treatment document
    data = _build_haken_ji_taigu_data(contract, kobetsu_emp, employee)

    service = TreatmentDocumentService()
    doc_bytes = service.generate_haken_ji_taigu_meijisho(data)

    emp_name = _get_employee_filename(employee)
    filename = f"派遣時待遇明示書_{emp_name}"
    return _document_response(doc_bytes, filename, format, subfolder="treatment")


@router.get("/employee/{employee_id}/yatoire-ji-taigu")
async def generate_yatoire_ji_taigu_meijisho(
    employee_id: int,
    format: str = Query("docx", description="Output format: 'docx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 雇入れ時の待遇情報明示書 (Treatment Info at Hiring).
    法第31条の2第2項の明示
    派遣元 → 派遣労働者 (when hiring the employee)

    This document is per-employee, not per-contract.

    Query params:
    - format: Output format ('docx' or 'pdf')
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Get the employee's most recent contract assignment for complaint handler info
    kobetsu_emp = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.employee_id == employee_id
    ).order_by(KobetsuEmployee.id.desc()).first()

    # Build data for hiring treatment document
    data = _build_yatoire_ji_taigu_data(employee, kobetsu_emp)

    service = TreatmentDocumentService()
    doc_bytes = service.generate_yatoire_ji_taigu_meijisho(data)

    emp_name = _get_employee_filename(employee)
    filename = f"雇入時待遇明示書_{emp_name}"
    return _document_response(doc_bytes, filename, format, subfolder="treatment")


@router.get("/factory/{factory_id}/shugyo-jokyo")
async def generate_shugyo_jokyo_hokokusho(
    factory_id: int,
    start_date: date = Query(..., description="Report period start date"),
    end_date: date = Query(..., description="Report period end date"),
    format: str = Query("docx", description="Output format: 'docx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 就業状況報告書 (Employment Status Report).
    派遣先 → 派遣元 (monthly report of dispatched workers status)

    Lists all dispatched workers at a factory during the specified period.

    Query params:
    - start_date: Report period start date (required)
    - end_date: Report period end date (required)
    - format: Output format ('docx' or 'pdf')
    """
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    service = EmploymentStatusReportService()

    try:
        doc_bytes = service.generate_shugyo_jokyo_hokokusho_from_db(
            db_session=db,
            factory_id=factory_id,
            start_date=start_date,
            end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Format filename with factory name and dates
    date_range = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    factory_name = (factory.plant_name or factory.company_name or f"factory_{factory_id}").replace(" ", "_")

    filename = f"就業状況報告書_{factory_name}_{date_range}"
    return _document_response(doc_bytes, filename, format, subfolder="reports")


# ========================================
# Helper functions
# ========================================

def _get_employee_filename(employee) -> str:
    """
    Get appropriate filename for employee based on nationality.
    - Japanese employees: 漢字 (kanji)
    - Foreign employees: カタカナ (katakana)
    - Fallback: employee_number
    """
    nationality = (employee.nationality or "").lower()
    is_japanese = nationality in ("japanese", "日本", "日本人", "japan", "jp")

    if is_japanese:
        # Japanese: use kanji name
        if employee.full_name_kanji:
            return employee.full_name_kanji.replace(" ", "_")
    else:
        # Foreigner: use katakana name
        if employee.full_name_kana:
            return employee.full_name_kana.replace(" ", "_")

    # Fallback to kanji, then kana, then romaji, then employee number
    if employee.full_name_kanji:
        return employee.full_name_kanji.replace(" ", "_")
    if employee.full_name_kana:
        return employee.full_name_kana.replace(" ", "_")
    if employee.full_name_romaji:
        return employee.full_name_romaji.replace(" ", "_")

    return str(employee.employee_number)


def _build_haken_ji_taigu_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee) -> dict:
    """Build data for 派遣時の待遇情報明示書."""
    from app.core.config import settings

    factory = contract.factory

    # Determine hourly wage
    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate

    return {
        "worker_name": employee.full_name_kanji or employee.full_name_romaji or "",
        "is_kyotei_taisho": contract.is_kyotei_taisho if contract.is_kyotei_taisho is not None else True,
        "kyotei_end_date": getattr(contract, 'kyotei_end_date', None) or date.today().replace(month=12, day=31),
        "wage_type": "hourly",
        "base_wage": float(hourly_wage) if hourly_wage else 0,
        "overtime_rate_under_60h": 25,  # Standard rate
        "overtime_rate_over_60h": 50,   # Over 60h rate
        "holiday_rate_percent": 35,      # Holiday rate
        "night_rate_percent": 25,        # Night work rate
        "has_raise": True,               # Default: has raise opportunity
        "has_bonus": False,              # Default: no bonus for dispatch workers
        "has_retirement_allowance": False,  # Default: no retirement allowance
        "yukyu_after_6months": 10,       # Standard paid leave after 6 months
        "yukyu_hourly": False,           # Default: no hourly paid leave
        "has_substitute_leave": False,   # Default: no substitute leave
        "other_leave": "",
        "allowances": [],  # Can add allowances if needed
    }


def _build_yatoire_ji_taigu_data(employee, kobetsu_emp=None) -> dict:
    """Build data for 雇入れ時の待遇情報明示書."""
    from app.core.config import settings

    # Get complaint handler info from most recent contract if available
    hakensaki_complaint_dept = ""
    hakensaki_complaint_name = ""
    hakensaki_complaint_phone = ""

    if kobetsu_emp and kobetsu_emp.kobetsu_keiyakusho:
        contract = kobetsu_emp.kobetsu_keiyakusho
        if contract.haken_saki_complaint_contact:
            complaint_info = contract.haken_saki_complaint_contact
            if isinstance(complaint_info, dict):
                hakensaki_complaint_dept = complaint_info.get('department', '')
                hakensaki_complaint_name = complaint_info.get('name', '')
                hakensaki_complaint_phone = complaint_info.get('phone', '')

    return {
        "document_date": date.today(),
        "worker_name": employee.full_name_kanji or employee.full_name_romaji or "",
        "is_kyotei_taisho": True,  # Default: agreement target worker
        "kyotei_end_date": date.today().replace(month=12, day=31),  # End of current year default
        "has_raise": True,
        "has_bonus": False,
        "has_retirement_allowance": False,
        "hakensaki_complaint_dept": hakensaki_complaint_dept,
        "hakensaki_complaint_name": hakensaki_complaint_name,
        "hakensaki_complaint_phone": hakensaki_complaint_phone,
        "hakenmoto_complaint_dept": settings.DISPATCH_COMPLAINT_DEPARTMENT,
        "hakenmoto_complaint_name": settings.DISPATCH_COMPLAINT_NAME,
        "hakenmoto_complaint_phone": settings.DISPATCH_COMPLAINT_PHONE,
    }


def _build_jinzai_haken_data(contract: KobetsuKeiyakusho, factory) -> dict:
    """Build data dictionary for 人材派遣個別契約書 exact PDF clone format."""
    from app.core.config import settings

    # Get hourly rate for calculations
    base_rate = float(contract.hourly_rate) if contract.hourly_rate else 1700

    return {
        # Client company info (派遣先)
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "client_address": factory.company_address if factory else contract.worksite_address,
        "client_tel": factory.company_tel if factory and hasattr(factory, 'company_tel') else "",

        # Worksite info (就業場所)
        "worksite_name": contract.worksite_name or (f"{factory.company_name} {factory.plant_name}" if factory else ""),
        "worksite_address": contract.worksite_address or (factory.plant_address if factory else ""),
        "worksite_tel": factory.company_tel if factory and hasattr(factory, 'company_tel') else "",

        # Organization unit and conflict date
        "organizational_unit": contract.organizational_unit or (factory.organizational_unit if factory and hasattr(factory, 'organizational_unit') else ""),
        "conflict_date": factory.conflict_date if factory else None,

        # Supervisor (指揮命令者)
        "supervisor_dept": contract.supervisor_department or "",
        "supervisor_position": contract.supervisor_position or "",
        "supervisor_name": contract.supervisor_name or "",
        "supervisor_tel": "",  # Can be added to model if needed

        # 派遣先責任者 (Destination manager)
        "saki_manager_dept": contract.haken_saki_manager.get('department', '') if contract.haken_saki_manager else "",
        "saki_manager_position": contract.haken_saki_manager.get('position', '') if contract.haken_saki_manager else "",
        "saki_manager_name": contract.haken_saki_manager.get('name', '') if contract.haken_saki_manager else "",
        "saki_manager_tel": contract.haken_saki_manager.get('phone', '') if contract.haken_saki_manager else "",

        # 派遣先苦情処理担当者
        "saki_complaint_dept": contract.haken_saki_complaint_contact.get('department', '') if contract.haken_saki_complaint_contact else "",
        "saki_complaint_position": contract.haken_saki_complaint_contact.get('position', '') if contract.haken_saki_complaint_contact else "",
        "saki_complaint_name": contract.haken_saki_complaint_contact.get('name', '') if contract.haken_saki_complaint_contact else "",
        "saki_complaint_tel": contract.haken_saki_complaint_contact.get('phone', '') if contract.haken_saki_complaint_contact else "",

        # 派遣元責任者 (Source manager) - defaults from settings
        "moto_manager_dept": contract.haken_moto_manager.get('department', settings.DISPATCH_RESPONSIBLE_DEPARTMENT) if contract.haken_moto_manager else settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
        "moto_manager_position": contract.haken_moto_manager.get('position', settings.DISPATCH_RESPONSIBLE_POSITION) if contract.haken_moto_manager else settings.DISPATCH_RESPONSIBLE_POSITION,
        "moto_manager_name": contract.haken_moto_manager.get('name', settings.DISPATCH_RESPONSIBLE_NAME) if contract.haken_moto_manager else settings.DISPATCH_RESPONSIBLE_NAME,
        "moto_manager_tel": contract.haken_moto_manager.get('phone', settings.DISPATCH_RESPONSIBLE_PHONE) if contract.haken_moto_manager else settings.DISPATCH_RESPONSIBLE_PHONE,

        # 派遣元苦情処理担当者
        "moto_complaint_dept": contract.haken_moto_complaint_contact.get('department', settings.DISPATCH_COMPLAINT_DEPARTMENT) if contract.haken_moto_complaint_contact else settings.DISPATCH_COMPLAINT_DEPARTMENT,
        "moto_complaint_position": contract.haken_moto_complaint_contact.get('position', settings.DISPATCH_COMPLAINT_POSITION) if contract.haken_moto_complaint_contact else settings.DISPATCH_COMPLAINT_POSITION,
        "moto_complaint_name": contract.haken_moto_complaint_contact.get('name', settings.DISPATCH_COMPLAINT_NAME) if contract.haken_moto_complaint_contact else settings.DISPATCH_COMPLAINT_NAME,
        "moto_complaint_tel": contract.haken_moto_complaint_contact.get('phone', settings.DISPATCH_COMPLAINT_PHONE) if contract.haken_moto_complaint_contact else settings.DISPATCH_COMPLAINT_PHONE,

        # Checkboxes
        "is_kyotei_gentei": contract.is_kyotei_taisho if contract.is_kyotei_taisho is not None else True,
        "is_kengen_nashi": True,  # Default: no special authority granted

        # Work content
        "work_content": contract.work_content or "機械オペレーター及び機械メンテナンス他付随する業務",

        # Dispatch period
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "number_of_workers": contract.number_of_workers or 1,

        # Work schedule
        "work_days_text": _format_work_days(contract.work_days) if contract.work_days else "月～金（祝日、年末年始、夏季休業を除く。）4勤2休シフト　別紙カレンダーの通り",
        "work_time_text": _format_work_time(contract) if contract.work_start_time else "昼勤：8時00分～17時00分　・　夜勤：20時00分～5時00分（実働　7時間40分）",
        "break_time_text": contract.break_time_detail if hasattr(contract, 'break_time_detail') and contract.break_time_detail else f"昼勤：10時00～10時15分・12時00分～12時50分・15時00分～15時15分　夜勤：22時00～22時15・00時00分～00時50分・03時00分～03時15分",

        # Overtime
        "holiday_work_limit": f"1ヶ月に{contract.holiday_work_max_days or 2}日の範囲内で命ずることができる。",
        "overtime_limit": f"{float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 5}時間/日、{float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45}時間/月、360時間/年迄とする。但し、特別条項の申請により、6時間/日、80時間/月、720時間/年迄延長できる。申請は6回/年迄とする。",

        # Rates
        "rate_basic": int(base_rate),
        "rate_overtime": int(float(contract.overtime_rate)) if contract.overtime_rate else int(base_rate * 1.25),
        "rate_night": int(float(contract.night_rate)) if hasattr(contract, 'night_rate') and contract.night_rate else int(base_rate * 1.25),
        "rate_holiday": int(float(contract.holiday_rate)) if contract.holiday_rate else int(base_rate * 1.35),
        "rate_over60": int(base_rate * 1.5),
        "calculation_unit": "5分単位",

        # Payment
        "payment_closing": "20日",
        "payment_date": "翌月20日",
        "payment_method": "銀行振込",
        "bank_info": "愛知銀行　お知支店　普通2075479　名義人　ユニバーサル企画（株）",

        # Contract date
        "contract_date": contract.contract_date or date.today(),
    }


def _format_work_days(work_days) -> str:
    """Format work days for display."""
    if isinstance(work_days, list):
        if len(work_days) >= 5:
            return "月～金（祝日、年末年始、夏季休業を除く。）4勤2休シフト　別紙カレンダーの通り"
        return '・'.join(work_days)
    return str(work_days) if work_days else "月～金（祝日、年末年始、夏季休業を除く。）"


def _format_work_time(contract) -> str:
    """Format work time for display."""
    start = contract.work_start_time
    end = contract.work_end_time
    if start and end:
        start_str = start.strftime("%H時%M分")
        end_str = end.strftime("%H時%M分")
        return f"昼勤：{start_str}～{end_str}（実働　7時間40分）"
    return "昼勤：8時00分～17時00分　・　夜勤：20時00分～5時00分（実働　7時間40分）"


def _build_contract_data(contract: KobetsuKeiyakusho) -> dict:
    """Build data dictionary from contract for document generation."""
    factory = contract.factory

    return {
        "contract_number": contract.contract_number,
        "contract_date": contract.contract_date,
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "client_address": factory.company_address if factory else contract.worksite_address,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "supervisor_dept": contract.supervisor_department,
        "supervisor_position": contract.supervisor_position,
        "supervisor_name": contract.supervisor_name,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,
        "hourly_rate": float(contract.hourly_rate),
        "overtime_rate": float(contract.overtime_rate),
        "holiday_rate": float(contract.holiday_rate) if contract.holiday_rate else float(contract.overtime_rate),
        "number_of_workers": contract.number_of_workers,
        "haken_moto_manager": contract.haken_moto_manager,
        "haken_saki_manager": contract.haken_saki_manager,
        "haken_moto_complaint": contract.haken_moto_complaint_contact,
        "haken_saki_complaint": contract.haken_saki_complaint_contact,
        "safety_measures": contract.safety_measures,
        "termination_measures": contract.termination_measures,
        "welfare_facilities": contract.welfare_facilities,
        "is_kyotei_taisho": contract.is_kyotei_taisho,
        "is_mukeiko_60over": contract.is_mukeiko_60over_only,
        "conflict_date": factory.conflict_date if factory else None,
    }


def _build_worker_condition_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee) -> dict:
    """Build worker condition data for 就業条件明示書."""
    factory = contract.factory

    # Determine hourly wage (employee individual > contract)
    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    overtime_wage = kobetsu_emp.overtime_rate or contract.overtime_rate

    return {
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "supervisor_name": contract.supervisor_name,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "overtime_wage": float(overtime_wage) if overtime_wage else 0,
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,
        "conflict_date": factory.conflict_date if factory else None,
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_agreement_target": contract.is_kyotei_taisho,
        "haken_moto_manager": contract.haken_moto_manager,
        "complaint_handler_moto": contract.haken_moto_complaint_contact,
        "complaint_handler_saki": contract.haken_saki_complaint_contact,
        "welfare_facilities": contract.welfare_facilities,
    }


def _build_notification_data(contract: KobetsuKeiyakusho, kobetsu_employees: list) -> dict:
    """Build notification data for 派遣通知書."""
    factory = contract.factory

    workers = []
    for ke in kobetsu_employees:
        emp = ke.employee
        workers.append({
            "worker_name": emp.full_name_kanji,
            "worker_gender": emp.gender or "男",
            "is_indefinite": ke.is_indefinite_employment or emp.is_indefinite_employment,
            "is_over_60": (emp.age or 0) >= 60 if emp.age else False,
            "has_health_insurance": emp.has_health_insurance,
            "has_pension": emp.has_pension_insurance,
            "has_employment_insurance": emp.has_employment_insurance,
            "is_agreement_target": contract.is_kyotei_taisho,
        })

    return {
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "workers": workers,
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "worksite_name": contract.worksite_name,
        "work_content": contract.work_content,
        "haken_moto_manager": contract.haken_moto_manager,
    }


def _build_ledger_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee, is_source: bool) -> dict:
    """Build ledger data for 管理台帳."""
    factory = contract.factory

    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    billing_rate = kobetsu_emp.billing_rate or employee.billing_rate or contract.hourly_rate

    return {
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,
        "worker_gender": employee.gender or "",
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_over_60": (employee.age or 0) >= 60 if employee.age else False,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "supervisor_name": contract.supervisor_name,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "is_agreement_target": contract.is_kyotei_taisho,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "billing_rate": float(billing_rate) if billing_rate else 0,
        "haken_moto_manager": contract.haken_moto_manager,
        "haken_saki_manager": contract.haken_saki_manager,
        "complaint_handler_moto": contract.haken_moto_complaint_contact,
        "complaint_handler_saki": contract.haken_saki_complaint_contact,
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,
        "welfare_facilities": contract.welfare_facilities,
        "conflict_date": factory.conflict_date if factory else None,
        "dispatch_company": None,  # Will use settings default
        "dispatch_address": None,  # Will use settings default
    }


def _build_combined_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee) -> dict:
    """Build combined data for 個別契約書 + 就業条件明示書 one-page document."""
    factory = contract.factory

    # Determine wages (employee individual > contract)
    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    overtime_wage = kobetsu_emp.overtime_rate or contract.overtime_rate

    return {
        # Contract info
        "contract_number": contract.contract_number,
        "contract_date": contract.contract_date,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "client_address": factory.company_address if factory else contract.worksite_address,
        "number_of_workers": contract.number_of_workers,

        # Worksite info
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,

        # Work content
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,

        # Supervisor
        "supervisor_dept": contract.supervisor_department,
        "supervisor_position": contract.supervisor_position,
        "supervisor_name": contract.supervisor_name,
        "supervisor_phone": "",

        # Work schedule
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,

        # Rates (for contract)
        "hourly_rate": float(contract.hourly_rate) if contract.hourly_rate else 0,
        "overtime_rate": float(contract.overtime_rate) if contract.overtime_rate else 0,
        "holiday_rate": float(contract.holiday_rate) if contract.holiday_rate else float(contract.overtime_rate) if contract.overtime_rate else 0,

        # Wages (for worker)
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "overtime_wage": float(overtime_wage) if overtime_wage else 0,
        "wage_closing": "月末",
        "wage_payment": "翌25日",

        # Managers
        "haken_moto_manager": contract.haken_moto_manager or {},
        "haken_saki_manager": contract.haken_saki_manager or {},
        "haken_moto_complaint": contract.haken_moto_complaint_contact or {},
        "haken_saki_complaint": contract.haken_saki_complaint_contact or {},

        # Safety and termination
        "safety_measures": contract.safety_measures,
        "termination_measures": contract.termination_measures,

        # Welfare
        "welfare_facilities": contract.welfare_facilities,

        # Worker info
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,

        # Insurance
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,

        # Employment status
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_over_60": (employee.age or 0) >= 60 if employee.age else False,
        "is_kyotei_taisho": contract.is_kyotei_taisho,
        "is_mukeiko_60over": contract.is_mukeiko_60over_only,

        # Conflict dates
        "conflict_date": factory.conflict_date if factory else None,
        "personal_conflict_date": kobetsu_emp.personal_conflict_date if hasattr(kobetsu_emp, 'personal_conflict_date') else None,

        # Scope changes (2024 requirement)
        "work_change_scope": "会社の定める業務",
        "location_change_scope": "会社の定める場所",

        # Renewal
        "renewal_policy": "更新する場合がある",
        "notes": "",
    }


# ========================================
# EXCEL-BASED DOCUMENT GENERATION
# ========================================

def _excel_response(
    xlsx_bytes: bytes,
    filename: str,
    output_format: str = "xlsx",
    save_copy: bool = True,
    subfolder: str = ""
) -> Response:
    """
    Create appropriate Response for Excel documents.

    Args:
        xlsx_bytes: Excel document bytes
        filename: Base filename (without extension)
        output_format: 'xlsx' or 'pdf'
        save_copy: Whether to save a copy to disk
        subfolder: Subfolder for saving

    Returns:
        FastAPI Response with correct content type
    """
    from urllib.parse import quote

    def get_content_disposition(fname: str) -> str:
        encoded = quote(fname, safe='')
        return f"attachment; filename*=UTF-8''{encoded}"

    if output_format.lower() == "pdf":
        try:
            # Convert Excel to PDF via LibreOffice
            pdf_bytes = _convert_xlsx_to_pdf(xlsx_bytes)
            full_filename = f"{filename}.pdf"

            if save_copy:
                _save_document(pdf_bytes, full_filename, subfolder)

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": get_content_disposition(full_filename)
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF conversion failed: {str(e)}. Try format=xlsx instead."
            )
    else:
        full_filename = f"{filename}.xlsx"

        if save_copy:
            _save_document(xlsx_bytes, full_filename, subfolder)

        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": get_content_disposition(full_filename)
            }
        )


def _convert_xlsx_to_pdf(xlsx_bytes: bytes, timeout: int = 60) -> bytes:
    """Convert Excel bytes to PDF via LibreOffice."""
    import tempfile
    import subprocess
    import os
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        xlsx_path = temp_path / "document.xlsx"
        xlsx_path.write_bytes(xlsx_bytes)

        user_profile = temp_path / "libreoffice_profile"
        user_profile.mkdir(exist_ok=True)

        env = os.environ.copy()
        env["HOME"] = str(temp_path)

        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--nofirststartwizard",
                f"-env:UserInstallation=file://{user_profile}",
                "--convert-to", "pdf",
                "--outdir", str(temp_path),
                str(xlsx_path)
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )

        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        pdf_path = temp_path / "document.pdf"
        if not pdf_path.exists():
            raise Exception("PDF file was not created")

        return pdf_path.read_bytes()


@router.get("/excel/{contract_id}/kobetsu-keiyakusho")
async def generate_excel_kobetsu_keiyakusho(
    contract_id: int,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 個別契約書 using Excel template.

    This version creates a STANDALONE document with ALL data filled in.
    All formulas are replaced with static values - no external dependencies.

    Query params:
    - format: 'xlsx' (default) or 'pdf'
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    factory = contract.factory

    # Build complete data dictionary for standalone Excel generation
    data = {
        # Company and factory info
        "company_name": factory.company_name if factory else contract.worksite_name,
        "company_address": factory.company_address if factory else "",
        "factory_name": factory.plant_name if factory else "",
        "factory_address": factory.plant_address if factory else "",
        "department": factory.organizational_unit if factory and hasattr(factory, 'organizational_unit') else "",
        "line": "",  # Optional line identifier

        # Worksite info
        "worksite_name": contract.worksite_name or (f"{factory.company_name} {factory.plant_name}" if factory else ""),
        "worksite_address": contract.worksite_address or (factory.plant_address if factory else ""),

        # Supervisor info
        "supervisor_name": contract.supervisor_name or "",
        "supervisor_department": contract.supervisor_department or "",
        "supervisor_position": contract.supervisor_position or "",

        # Manufacturing manager (派遣先責任者)
        "mfg_manager_name": contract.haken_saki_manager.get('name', '') if contract.haken_saki_manager else "",
        "mfg_manager_department": contract.haken_saki_manager.get('department', '') if contract.haken_saki_manager else "",
        "mfg_manager_position": contract.haken_saki_manager.get('position', '') if contract.haken_saki_manager else "",

        # Complaint handler (派遣先)
        "complaint_handler_name": contract.haken_saki_complaint_contact.get('name', '') if contract.haken_saki_complaint_contact else "",
        "complaint_handler_dept": contract.haken_saki_complaint_contact.get('department', '') if contract.haken_saki_complaint_contact else "",
        "complaint_handler_pos": contract.haken_saki_complaint_contact.get('position', '') if contract.haken_saki_complaint_contact else "",

        # Work content
        "work_content": contract.work_content or "機械オペレーター及び機械メンテナンス他付随する業務",

        # Dispatch period
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "num_workers": contract.number_of_workers or 1,

        # Work schedule
        "work_days_text": _format_work_days(contract.work_days) if contract.work_days else "月～金（祝日、年末年始、夏季休業を除く。）",
        "work_start_time": contract.work_start_time.strftime("%H:%M") if contract.work_start_time else "08:00",
        "work_end_time": contract.work_end_time.strftime("%H:%M") if contract.work_end_time else "17:00",
        "break_duration_minutes": contract.break_time_minutes or 60,
        "break_time_text": f"{contract.break_time_minutes or 60}分",

        # Overtime
        "overtime_hours_per_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_hours_per_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "overtime_text": f"1日{float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4}時間、1ヶ月{float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45}時間を限度とする",

        # Rates
        "hourly_rate": float(contract.hourly_rate) if contract.hourly_rate else 1700,

        # Restriction date
        "restriction_date": factory.conflict_date.strftime("%Y年%m月%d日") if factory and factory.conflict_date else "",
    }

    # Generate standalone Excel document
    xlsx_bytes = KobetsuExcelGenerator.generate(data)

    factory_name = (factory.plant_name or factory.company_name if factory else "").replace(" ", "_")
    filename = f"個別契約書_{factory_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="contracts")


@router.get("/excel2/{contract_id}/tsuchisho")
async def generate_excel2_tsuchisho(
    contract_id: int,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 通知書 (Notification) using NEW Excel generator (Sheet 2).

    This version creates a STANDALONE document with ALL data filled in.
    All formulas are replaced with static values - no external dependencies.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    factory = contract.factory

    # Get employees for this contract
    kobetsu_employees = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
    ).all()

    # Build data dictionary
    data = _build_excel_document_data(contract, factory, kobetsu_employees)

    xlsx_bytes = KobetsuExcelGenerator.generate_tsuchisho(data)

    factory_name = (factory.plant_name or factory.company_name if factory else "").replace(" ", "_")
    filename = f"通知書_{factory_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="notifications")


@router.get("/excel2/{contract_id}/daicho")
async def generate_excel2_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate DAICHO (派遣先管理台帳 - Registry) using NEW Excel generator (Sheet 3).

    This is the destination registry for tracking dispatched workers.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    factory = contract.factory

    # Build data dictionary with employee info
    data = _build_excel_document_data(contract, factory, [kobetsu_emp])
    data.update(_build_employee_data(employee, kobetsu_emp))

    xlsx_bytes = KobetsuExcelGenerator.generate_daicho(data)

    emp_name = employee.full_name_kanji or employee.employee_number
    filename = f"DAICHO_{emp_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="ledgers")


@router.get("/excel2/{contract_id}/hakenmoto-daicho")
async def generate_excel2_hakenmoto_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 派遣元管理台帳 (Dispatch Origin Registry) using NEW Excel generator (Sheet 4).

    This is the source company's registry for tracking dispatched workers.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    factory = contract.factory

    data = _build_excel_document_data(contract, factory, [kobetsu_emp])
    data.update(_build_employee_data(employee, kobetsu_emp))

    xlsx_bytes = KobetsuExcelGenerator.generate_hakenmoto_daicho(data)

    emp_name = employee.full_name_kanji or employee.employee_number
    filename = f"派遣元管理台帳_{emp_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="ledgers")


@router.get("/excel2/{contract_id}/shugyo-joken")
async def generate_excel2_shugyo_joken(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 就業条件明示書 (Employment Conditions Statement) using NEW Excel generator (Sheet 5).

    This document clarifies employment conditions for the dispatched worker.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    factory = contract.factory

    data = _build_excel_document_data(contract, factory, [kobetsu_emp])
    data.update(_build_employee_data(employee, kobetsu_emp))

    xlsx_bytes = KobetsuExcelGenerator.generate_shugyo_joken(data)

    emp_name = employee.full_name_kanji or employee.employee_number
    filename = f"就業条件明示書_{emp_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="conditions")


@router.get("/excel2/{contract_id}/keiyakusho")
async def generate_excel2_keiyakusho(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 契約書 (Employment Contract) using NEW Excel generator (Sheet 6).

    This is the employment contract document between the dispatch company and worker.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    factory = contract.factory

    data = _build_excel_document_data(contract, factory, [kobetsu_emp])
    data.update(_build_employee_data(employee, kobetsu_emp))
    data["contract_date"] = contract.contract_date
    data["contract_start_date"] = contract.dispatch_start_date
    data["contract_end_date"] = contract.dispatch_end_date

    xlsx_bytes = KobetsuExcelGenerator.generate_keiyakusho(data)

    emp_name = employee.full_name_kanji or employee.employee_number
    filename = f"契約書_{emp_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="contracts")


def _build_excel_document_data(contract: KobetsuKeiyakusho, factory, kobetsu_employees: list) -> dict:
    """
    Build common data dictionary for all Excel-based documents.
    """
    return {
        # Company and factory info
        "company_name": factory.company_name if factory else contract.worksite_name,
        "company_address": factory.company_address if factory else "",
        "factory_name": factory.plant_name if factory else "",
        "factory_address": factory.plant_address if factory else "",
        "department": factory.organizational_unit if factory and hasattr(factory, 'organizational_unit') else "",
        "line": "",

        # Worksite info
        "worksite_name": contract.worksite_name or (f"{factory.company_name} {factory.plant_name}" if factory else ""),
        "worksite_address": contract.worksite_address or (factory.plant_address if factory else ""),
        "organizational_unit": contract.organizational_unit or "",

        # Supervisor info
        "supervisor_name": contract.supervisor_name or "",
        "supervisor_department": contract.supervisor_department or "",
        "supervisor_position": contract.supervisor_position or "",

        # Manufacturing manager (派遣先責任者)
        "mfg_manager_name": contract.haken_saki_manager.get('name', '') if contract.haken_saki_manager else "",
        "mfg_manager_department": contract.haken_saki_manager.get('department', '') if contract.haken_saki_manager else "",
        "mfg_manager_position": contract.haken_saki_manager.get('position', '') if contract.haken_saki_manager else "",

        # Complaint handlers
        "complaint_handler_name": contract.haken_saki_complaint_contact.get('name', '') if contract.haken_saki_complaint_contact else "",
        "complaint_handler_dept": contract.haken_saki_complaint_contact.get('department', '') if contract.haken_saki_complaint_contact else "",
        "complaint_handler_pos": contract.haken_saki_complaint_contact.get('position', '') if contract.haken_saki_complaint_contact else "",
        "client_complaint_handler": contract.haken_saki_complaint_contact.get('name', '') if contract.haken_saki_complaint_contact else "",

        # Work content
        "work_content": contract.work_content or "機械オペレーター及び機械メンテナンス他付随する業務",

        # Dispatch period
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "num_workers": contract.number_of_workers or 1,

        # Work schedule
        "work_days_text": _format_work_days(contract.work_days) if contract.work_days else "月～金（祝日、年末年始、夏季休業を除く。）",
        "work_start_time": contract.work_start_time.strftime("%H:%M") if contract.work_start_time else "08:00",
        "work_end_time": contract.work_end_time.strftime("%H:%M") if contract.work_end_time else "17:00",
        "work_hours_text": f"{contract.work_start_time.strftime('%H:%M') if contract.work_start_time else '08:00'} ～ {contract.work_end_time.strftime('%H:%M') if contract.work_end_time else '17:00'}",
        "break_duration_minutes": contract.break_time_minutes or 60,
        "break_time_text": f"{contract.break_time_minutes or 60}分",

        # Overtime
        "overtime_hours_per_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_hours_per_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "overtime_text": f"1日{float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4}時間、1ヶ月{float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45}時間を限度とする",
        "holidays_text": "土曜日、日曜日、祝日、年末年始、夏季休暇",

        # Rates
        "hourly_rate": float(contract.hourly_rate) if contract.hourly_rate else 1700,
        "payment_date": "翌月25日",

        # Restriction date
        "restriction_date": factory.conflict_date.strftime("%Y年%m月%d日") if factory and factory.conflict_date else "",

        # Issue/created dates
        "issue_date": date.today(),
        "created_date": date.today(),
        "dispatch_date_text": date.today().strftime("%Y年%m月%d日"),
    }


def _build_employee_data(employee, kobetsu_emp) -> dict:
    """
    Build employee-specific data for documents.
    """
    return {
        "employee_name": employee.full_name_kanji or employee.full_name_kana or "",
        "employee_katakana": employee.full_name_kana or "",
        "employee_number": employee.employee_number or "",
        "employee_dob": employee.date_of_birth,
        "employee_gender": employee.gender or "",
        "employee_address": employee.address or "",
        "employee_phone": employee.phone_number or "",

        # Work location for keiyakusho
        "work_location": f"{kobetsu_emp.kobetsu_keiyakusho.worksite_name}" if kobetsu_emp and kobetsu_emp.kobetsu_keiyakusho else "",
    }


@router.get("/excel/{contract_id}/tsuchisho")
async def generate_excel_tsuchisho(
    contract_id: int,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 通知書 (Dispatch Notification) using Excel template.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    factory = contract.factory

    # Build data dict
    data = _build_jinzai_haken_data(contract, factory)

    # Get employees for notification
    kobetsu_employees = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
    ).all()

    employees = []
    for ke in kobetsu_employees:
        emp = ke.employee
        if emp:
            employees.append({
                "name": emp.full_name_kanji or emp.full_name_kana,
                "kana": emp.full_name_kana or "",
            })
    data["employees"] = employees

    service = ExcelDocumentService()
    xlsx_bytes = service.generate_tsuchisho(data)

    factory_name = (factory.plant_name or factory.company_name if factory else "").replace(" ", "_")
    filename = f"通知書_{factory_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="notifications")


@router.get("/excel/{contract_id}/hakenmoto-daicho")
async def generate_excel_hakenmoto_daicho(
    contract_id: int,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 派遣元管理台帳 (Dispatch Origin Ledger) using Excel template.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    factory = contract.factory

    data = _build_jinzai_haken_data(contract, factory)
    data["contract_number"] = contract.contract_number

    service = ExcelDocumentService()
    xlsx_bytes = service.generate_hakenmoto_daicho(data)

    factory_name = (factory.plant_name or factory.company_name if factory else "").replace(" ", "_")
    filename = f"派遣元管理台帳_{factory_name}_{contract.contract_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="ledgers")


@router.get("/excel/{contract_id}/shugyo-joken")
async def generate_excel_shugyo_joken(
    contract_id: int,
    employee_id: Optional[int] = None,
    format: str = Query("xlsx", description="Output format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate 就業条件明示書 (Employment Conditions Document) using Excel template.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    factory = contract.factory

    data = _build_jinzai_haken_data(contract, factory)
    data["employee_name"] = employee.full_name_kanji or employee.full_name_kana
    data["hourly_rate"] = kobetsu_emp.hourly_rate or contract.hourly_rate
    data["overtime_rate"] = kobetsu_emp.overtime_rate or contract.overtime_rate

    service = ExcelDocumentService()
    xlsx_bytes = service.generate_shugyo_joken(data)

    filename = f"就業条件明示書_{employee.employee_number}"

    return _excel_response(xlsx_bytes, filename, format, subfolder="conditions")


@router.get("/excel/templates/status")
async def get_excel_templates_status(
    current_user: dict = Depends(get_current_user),
):
    """
    Check status of Excel templates.

    Returns information about available templates and their status.
    """
    from app.services.template_manager import TemplateManager

    templates = TemplateManager.list_templates()
    all_valid, missing = TemplateManager.validate_templates()

    return {
        "all_valid": all_valid,
        "missing_templates": missing,
        "templates": templates,
    }
