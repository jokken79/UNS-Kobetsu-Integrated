"""
Document Data Schema - JSON format for generating all legal documents.

This schema serves as the intermediate format between database models
and document generation (Excel, PDF, HTML).
"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PersonInfo(BaseModel):
    """Person information (manager, supervisor, etc.)"""
    name: str
    name_kana: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CompanyInfo(BaseModel):
    """Company information (dispatch origin or destination)"""
    name: str
    name_legal: Optional[str] = None
    postal_code: Optional[str] = None
    address: str
    tel: str
    fax: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None  # For dispatch companies


class WorkSchedule(BaseModel):
    """Work schedule details"""
    work_days: List[str] = Field(default=["月", "火", "水", "木", "金"])
    work_start_time: time
    work_end_time: time
    break_time_minutes: int = 60
    overtime_max_hours_day: int = 4
    overtime_max_hours_month: int = 45


class RateInfo(BaseModel):
    """Compensation rates"""
    hourly_rate: Decimal
    overtime_rate: Optional[Decimal] = None
    holiday_rate: Optional[Decimal] = None
    night_shift_rate: Optional[Decimal] = None
    transport_allowance: Optional[Decimal] = None


class EmployeeData(BaseModel):
    """Employee information for documents"""
    employee_number: str
    full_name: str
    full_name_kana: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rate: Optional[RateInfo] = None


class DocumentDataSchema(BaseModel):
    """
    Complete data structure for generating all dispatch documents.

    This schema contains ALL information needed for:
    - 個別契約書 (Individual Dispatch Contract)
    - 通知書 (Notification)
    - DAICHO (Registry)
    - 派遣元管理台帳 (Dispatch Origin Ledger)
    - 就業条件明示書 (Employment Conditions)
    - 契約書 (Labor Contract)
    """

    # ========================================
    # CONTRACT IDENTIFICATION
    # ========================================
    contract_number: str = Field(..., description="Contract ID (e.g., KOB-202512-0001)")
    contract_date: date = Field(..., description="Date contract was signed")
    document_date: Optional[date] = Field(None, description="Document generation date")

    # ========================================
    # DISPATCH PERIOD (労働者派遣期間)
    # ========================================
    dispatch_start_date: date = Field(..., description="Start date of dispatch")
    dispatch_end_date: date = Field(..., description="End date of dispatch")

    # ========================================
    # DISPATCH COMPANY (派遣元)
    # ========================================
    dispatch_company: CompanyInfo = Field(..., description="Dispatch origin company (UNS Kikaku)")
    dispatch_manager: PersonInfo = Field(..., description="Dispatch origin manager (派遣元責任者)")
    dispatch_complaint_handler: PersonInfo = Field(..., description="Complaint handler at dispatch company")

    # ========================================
    # CLIENT COMPANY (派遣先)
    # ========================================
    client_company: CompanyInfo = Field(..., description="Client/destination company")
    client_manager: PersonInfo = Field(..., description="Client company manager (派遣先責任者)")
    client_complaint_handler: PersonInfo = Field(..., description="Complaint handler at client company")

    # ========================================
    # WORKSITE DETAILS (就業場所)
    # ========================================
    worksite_name: str = Field(..., description="Name of worksite (may differ from company)")
    worksite_address: str = Field(..., description="Physical address of worksite")
    organizational_unit: Optional[str] = Field(None, description="Department/division (組織単位)")
    production_line: Optional[str] = Field(None, description="Production line (ライン)")

    # ========================================
    # WORK CONTENT (業務内容)
    # ========================================
    work_content: str = Field(..., description="Detailed description of work to be performed")
    responsibility_level: str = Field(
        default="通常業務",
        description="Level of responsibility (e.g., 通常業務, 管理業務)"
    )

    # ========================================
    # SUPERVISION (指揮命令者)
    # ========================================
    supervisor: PersonInfo = Field(..., description="Person giving direct instructions")

    # ========================================
    # WORK SCHEDULE (就業時間)
    # ========================================
    schedule: WorkSchedule = Field(..., description="Work schedule details")

    # ========================================
    # COMPENSATION (派遣料金)
    # ========================================
    rates: RateInfo = Field(..., description="Compensation rates")

    # ========================================
    # EMPLOYEES (派遣労働者)
    # ========================================
    employees: List[EmployeeData] = Field(..., description="List of dispatched employees")
    number_of_workers: int = Field(..., description="Total number of workers in this contract")

    # ========================================
    # SAFETY & WELFARE (安全衛生・福利厚生)
    # ========================================
    safety_measures: str = Field(
        default="派遣先の安全衛生規程に従う",
        description="Safety and health measures"
    )
    welfare_facilities: List[str] = Field(
        default=["食堂", "更衣室", "休憩室"],
        description="Available welfare facilities"
    )

    # ========================================
    # LEGAL COMPLIANCE (法令遵守)
    # ========================================
    is_kyotei_taisho: bool = Field(default=False, description="Subject to kyotei (協定対象)")
    is_mukeiko_60over_only: bool = Field(
        default=False,
        description="Only for age 60+ without employment contract (無期雇用60歳以上)"
    )
    is_direct_hire_prevention: bool = Field(
        default=False,
        description="Direct hire prevention clause (紹介予定派遣)"
    )

    # ========================================
    # ADDITIONAL METADATA
    # ========================================
    notes: Optional[str] = Field(None, description="Additional notes or special conditions")
    created_by: Optional[str] = Field(None, description="User who created this document")
    version: str = Field(default="1.0", description="Document version")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_number": "KOB-202512-0001",
                "contract_date": "2025-12-01",
                "dispatch_start_date": "2025-12-15",
                "dispatch_end_date": "2026-12-14",
                "dispatch_company": {
                    "name": "UNS企画",
                    "address": "東京都...",
                    "tel": "03-1234-5678",
                    "license_number": "派13-123456"
                },
                "client_company": {
                    "name": "トヨタ自動車",
                    "address": "愛知県豊田市...",
                    "tel": "0565-12-3456"
                },
                "worksite_name": "豊田工場 第1製造部",
                "worksite_address": "愛知県豊田市本社1-1",
                "work_content": "自動車部品の組立作業",
                "supervisor": {
                    "name": "山田太郎",
                    "department": "製造部",
                    "position": "課長"
                },
                "schedule": {
                    "work_days": ["月", "火", "水", "木", "金"],
                    "work_start_time": "08:30",
                    "work_end_time": "17:30",
                    "break_time_minutes": 60
                },
                "rates": {
                    "hourly_rate": 1500
                },
                "employees": [
                    {
                        "employee_number": "E001",
                        "full_name": "田中花子",
                        "full_name_kana": "タナカハナコ"
                    }
                ],
                "number_of_workers": 1
            }
        }
