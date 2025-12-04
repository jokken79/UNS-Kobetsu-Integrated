"""
Documents V2 API - New JSON-based document generation endpoints.

This is the NEW architecture:
    DB Model → JSON Schema → Excel/PDF Generator → Download

Benefits:
- Testable (validate JSON separately)
- Flexible (same JSON for multiple formats)
- Maintainable (separate data from presentation)
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from typing import Literal

from app.api.deps import get_db
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.services.document_data_service import DocumentDataService
from app.services.excel_generator_v2 import ExcelGeneratorV2
from app.services.pdf_generator_v2 import PDFGeneratorV2


router = APIRouter()


@router.get("/{contract_id}/json")
def get_contract_as_json(
    contract_id: int = Path(..., description="Contract ID"),
    db: Session = Depends(get_db),
):
    """
    Get contract data as JSON (DocumentDataSchema format).

    This endpoint returns the normalized JSON format that feeds
    into both Excel and PDF generators.

    Use this to:
    - Preview data before generating documents
    - Debug document generation issues
    - Test JSON schema validity
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    try:
        json_data = DocumentDataService.to_json_dict(contract, db)
        return JSONResponse(content=json_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert contract to JSON: {str(e)}"
        )


@router.get("/{contract_id}/excel/{document_type}")
def generate_excel_document(
    contract_id: int = Path(..., description="Contract ID"),
    document_type: Literal[
        "kobetsu_keiyakusho",
        "tsuchisho",
        "daicho",
        "hakenmoto_daicho",
        "shugyo_joken",
        "keiyakusho",
    ] = Path(..., description="Type of document to generate"),
    db: Session = Depends(get_db),
):
    """
    Generate Excel document from contract.

    Available document types:
    - kobetsu_keiyakusho: 個別契約書 (Individual Dispatch Contract)
    - tsuchisho: 通知書 (Notification)
    - daicho: DAICHO (Registry)
    - hakenmoto_daicho: 派遣元管理台帳 (Dispatch Origin Ledger)
    - shugyo_joken: 就業条件明示書 (Employment Conditions)
    - keiyakusho: 契約書 (Labor Contract)

    Returns:
        Excel file (.xlsx) ready for download
    """
    # Load contract
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    try:
        # Convert to JSON
        json_schema = DocumentDataService.from_kobetsu_contract(contract, db)

        # Generate Excel
        generator = ExcelGeneratorV2(json_schema)

        if document_type == "kobetsu_keiyakusho":
            excel_bytes = generator.generate_kobetsu_keiyakusho()
        elif document_type == "tsuchisho":
            excel_bytes = generator.generate_tsuchisho()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Document type '{document_type}' not yet implemented for Excel"
            )

        # Return as downloadable file
        filename = f"{contract.contract_number}_{document_type}.xlsx"
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e) + "\n\nPlease run: python backend/scripts/extract_templates.py"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel document: {str(e)}"
        )


@router.get("/{contract_id}/pdf/{document_type}")
def generate_pdf_document(
    contract_id: int = Path(..., description="Contract ID"),
    document_type: Literal[
        "kobetsu_keiyakusho",
        "tsuchisho",
        "daicho",
    ] = Path(..., description="Type of document to generate"),
    db: Session = Depends(get_db),
):
    """
    Generate PDF document from contract.

    Available document types:
    - kobetsu_keiyakusho: 個別契約書 (Individual Dispatch Contract)
    - tsuchisho: 通知書 (Notification)
    - daicho: DAICHO (Registry)

    Returns:
        PDF file ready for download
    """
    # Load contract
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    try:
        # Convert to JSON
        json_schema = DocumentDataService.from_kobetsu_contract(contract, db)

        # Generate PDF
        generator = PDFGeneratorV2(json_schema)

        if document_type == "kobetsu_keiyakusho":
            pdf_bytes = generator.generate_kobetsu_keiyakusho()
        elif document_type == "tsuchisho":
            pdf_bytes = generator.generate_tsuchisho()
        elif document_type == "daicho":
            pdf_bytes = generator.generate_daicho()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown document type: {document_type}"
            )

        # Return as downloadable file
        filename = f"{contract.contract_number}_{document_type}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF document: {str(e)}"
        )


@router.get("/{contract_id}/all")
def generate_all_documents(
    contract_id: int = Path(..., description="Contract ID"),
    format: Literal["excel", "pdf", "both"] = Query(
        default="both",
        description="Format to generate"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate all available documents for a contract.

    Args:
        contract_id: Contract ID
        format: 'excel', 'pdf', or 'both'

    Returns:
        JSON with download URLs for each generated document
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    try:
        # Convert to JSON
        json_schema = DocumentDataService.from_kobetsu_contract(contract, db)

        results = {
            "contract_id": contract_id,
            "contract_number": contract.contract_number,
            "documents": []
        }

        # Generate Excel documents
        if format in ["excel", "both"]:
            excel_gen = ExcelGeneratorV2(json_schema)
            excel_docs = excel_gen.generate_all()

            for doc_name, doc_bytes in excel_docs.items():
                if "_error" in doc_name:
                    results["documents"].append({
                        "name": doc_name,
                        "format": "excel",
                        "status": "error",
                        "error": doc_bytes
                    })
                else:
                    results["documents"].append({
                        "name": doc_name,
                        "format": "excel",
                        "status": "success",
                        "url": f"/api/v1/documents-v2/{contract_id}/excel/{doc_name}",
                        "size_kb": len(doc_bytes) / 1024
                    })

        # Generate PDF documents
        if format in ["pdf", "both"]:
            pdf_gen = PDFGeneratorV2(json_schema)
            pdf_docs = pdf_gen.generate_all()

            for doc_name, doc_bytes in pdf_docs.items():
                if "_error" in doc_name:
                    results["documents"].append({
                        "name": doc_name,
                        "format": "pdf",
                        "status": "error",
                        "error": doc_bytes
                    })
                else:
                    results["documents"].append({
                        "name": doc_name,
                        "format": "pdf",
                        "status": "success",
                        "url": f"/api/v1/documents-v2/{contract_id}/pdf/{doc_name}",
                        "size_kb": len(doc_bytes) / 1024
                    })

        return results

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate documents: {str(e)}"
        )
