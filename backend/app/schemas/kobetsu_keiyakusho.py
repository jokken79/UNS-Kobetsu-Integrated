# backend/app/schemas/kobetsu_keiyakusho.py
"""
個別契約書 (Kobetsu Keiyakusho) Schemas
Pydantic models for API validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from decimal import Decimal


# ========================================
# BASE SCHEMAS
# ========================================

class ContactInfo(BaseModel):
    """連絡先情報"""
    department: str = Field(..., min_length=1, max_length=100, description="部署名")
    position: str = Field(..., min_length=1, max_length=100, description="役職")
    name: str = Field(..., min_length=1, max_length=100, description="氏名")
    phone: str = Field(..., pattern=r"^\d{2,4}-\d{2,4}-\d{4}$", description="電話番号")


class ManagerInfo(BaseModel):
    """責任者情報"""
    department: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., pattern=r"^\d{2,4}-\d{2,4}-\d{4}$")
    license_number: Optional[str] = Field(None, description="派遣元/先責任者講習修了証番号")


# ========================================
# CREATE SCHEMA
# ========================================

class KobetsuKeiyakushoCreate(BaseModel):
    """個別契約書作成用スキーマ"""
    
    # Relaciones
    factory_id: int = Field(..., gt=0)
    dispatch_assignment_id: Optional[int] = Field(None, gt=0)
    previous_contract_id: Optional[int] = Field(None, gt=0, description="Previous contract ID for renewals")
    employee_ids: List[int] = Field(..., min_items=1, description="派遣労働者IDリスト")
    
    # 基本情報
    contract_date: date = Field(..., description="契約締結日")
    dispatch_start_date: date = Field(..., description="派遣開始日")
    dispatch_end_date: date = Field(..., description="派遣終了日")
    
    # 業務内容
    work_content: str = Field(..., min_length=10, description="業務内容の詳細")
    responsibility_level: str = Field(
        ..., 
        description="責任の程度: 補助的業務, 通常業務, 責任業務"
    )
    
    # 派遣先情報
    worksite_name: str = Field(..., min_length=1, max_length=255)
    worksite_address: str = Field(..., min_length=10)
    organizational_unit: Optional[str] = Field(None, max_length=100, description="組織単位")
    
    # 指揮命令者
    supervisor_department: str = Field(..., min_length=1, max_length=100)
    supervisor_position: str = Field(..., min_length=1, max_length=100)
    supervisor_name: str = Field(..., min_length=1, max_length=100)
    
    # 就業条件
    work_days: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=7,
        description="就業日: ['月', '火', '水', '木', '金']"
    )
    work_start_time: time = Field(..., description="始業時刻")
    work_end_time: time = Field(..., description="終業時刻")
    break_time_minutes: int = Field(..., ge=0, le=180, description="休憩時間（分）")
    
    # 時間外労働
    overtime_max_hours_day: Optional[Decimal] = Field(None, ge=0, le=24)
    overtime_max_hours_month: Optional[Decimal] = Field(None, ge=0, le=200)
    overtime_max_days_month: Optional[int] = Field(None, ge=0, le=31)
    holiday_work_max_days: Optional[int] = Field(None, ge=0, le=12)
    
    # 安全衛生
    safety_measures: Optional[str] = Field(None, description="安全衛生に関する措置")
    
    # 苦情処理
    haken_moto_complaint_contact: ContactInfo
    haken_saki_complaint_contact: ContactInfo
    
    # 派遣料金
    hourly_rate: Decimal = Field(..., ge=1000, le=10000, description="時間単価")
    overtime_rate: Decimal = Field(..., ge=1000, le=15000, description="時間外単価")
    night_shift_rate: Optional[Decimal] = Field(None, ge=1000, le=15000)
    holiday_rate: Optional[Decimal] = Field(None, ge=1000, le=20000)
    
    # 福利厚生
    welfare_facilities: Optional[List[str]] = Field(
        None,
        description="福利厚生施設: ['食堂', '更衣室', '休憩室']"
    )
    
    # 責任者
    haken_moto_manager: ManagerInfo
    haken_saki_manager: ManagerInfo
    
    # 契約解除
    termination_measures: Optional[str] = Field(None, description="契約解除時の雇用安定措置")
    
    # その他
    is_kyotei_taisho: bool = Field(default=False, description="労使協定方式対象")
    is_direct_hire_prevention: bool = Field(default=False, description="直接雇用防止措置")
    is_mukeiko_60over_only: bool = Field(default=False, description="無期雇用・60歳以上限定")
    
    # メモ
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('dispatch_end_date')
    def validate_dates(cls, v, values):
        if 'dispatch_start_date' in values and v < values['dispatch_start_date']:
            raise ValueError('dispatch_end_date must be >= dispatch_start_date')
        return v
    
    @validator('work_end_time')
    def validate_work_times(cls, v, values):
        if 'work_start_time' in values and v <= values['work_start_time']:
            raise ValueError('work_end_time must be > work_start_time')
        return v
    
    @validator('responsibility_level')
    def validate_responsibility_level(cls, v):
        allowed = ["補助的業務", "通常業務", "責任業務"]
        if v not in allowed:
            raise ValueError(f'responsibility_level must be one of: {allowed}')
        return v
    
    @validator('work_days')
    def validate_work_days(cls, v):
        allowed_days = ["月", "火", "水", "木", "金", "土", "日"]
        for day in v:
            if day not in allowed_days:
                raise ValueError(f'Invalid day: {day}. Must be one of: {allowed_days}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "factory_id": 1,
                "employee_ids": [1, 2, 3],
                "contract_date": "2024-11-25",
                "dispatch_start_date": "2024-12-01",
                "dispatch_end_date": "2025-11-30",
                "work_content": "製造ライン作業、検品、梱包業務",
                "responsibility_level": "通常業務",
                "worksite_name": "トヨタ自動車株式会社 田原工場",
                "worksite_address": "愛知県田原市緑が浜2号1番地",
                "organizational_unit": "第1製造部",
                "supervisor_department": "製造部",
                "supervisor_position": "課長",
                "supervisor_name": "田中太郎",
                "work_days": ["月", "火", "水", "木", "金"],
                "work_start_time": "08:00",
                "work_end_time": "17:00",
                "break_time_minutes": 60,
                "hourly_rate": 1500,
                "overtime_rate": 1875
            }
        }


# ========================================
# UPDATE SCHEMA
# ========================================

class KobetsuKeiyakushoUpdate(BaseModel):
    """個別契約書更新用スキーマ"""

    previous_contract_id: Optional[int] = Field(None, gt=0, description="Previous contract ID for renewals")
    contract_date: Optional[date] = None
    dispatch_end_date: Optional[date] = None
    work_content: Optional[str] = Field(None, min_length=10)
    responsibility_level: Optional[str] = None
    supervisor_name: Optional[str] = None
    work_days: Optional[List[str]] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=1000, le=10000)
    overtime_rate: Optional[Decimal] = Field(None, ge=1000, le=15000)
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed = ["draft", "active", "expired", "cancelled", "renewed"]
            if v not in allowed:
                raise ValueError(f'status must be one of: {allowed}')
        return v


# ========================================
# RESPONSE SCHEMAS
# ========================================

class EmployeeBasicInfo(BaseModel):
    """従業員基本情報 (from Employee model)"""
    id: int
    employee_number: str  # 社員№
    full_name_kanji: Optional[str] = None  # 漢字氏名
    full_name_kana: Optional[str] = None  # カナ氏名
    full_name_romaji: Optional[str] = None  # ローマ字氏名
    nationality: Optional[str] = None  # 国籍

    class Config:
        from_attributes = True


class KobetsuEmployeeInfo(BaseModel):
    """契約に紐づく従業員情報 (from KobetsuEmployee join table)"""
    id: int  # KobetsuEmployee.id
    employee_id: int  # FK to employees
    hourly_rate: Optional[Decimal] = None  # 個別時給
    individual_start_date: Optional[date] = None  # 途中入社日
    individual_end_date: Optional[date] = None  # 途中退社日
    is_indefinite_employment: bool = False  # 無期雇用

    # Nested employee info
    employee: Optional[EmployeeBasicInfo] = None

    class Config:
        from_attributes = True


class KobetsuKeiyakushoResponse(BaseModel):
    """個別契約書レスポンス"""
    
    id: int
    factory_id: int
    dispatch_assignment_id: Optional[int]
    previous_contract_id: Optional[int]

    # 基本情報
    contract_number: str
    contract_date: date
    dispatch_start_date: date
    dispatch_end_date: date
    
    # 業務内容
    work_content: str
    responsibility_level: str
    
    # 派遣先
    worksite_name: str
    worksite_address: str
    organizational_unit: Optional[str]
    
    # 指揮命令者
    supervisor_department: str
    supervisor_position: str
    supervisor_name: str
    
    # 就業条件
    work_days: List[str]
    work_start_time: time
    work_end_time: time
    break_time_minutes: int
    
    # 時間外
    overtime_max_hours_day: Optional[Decimal]
    overtime_max_hours_month: Optional[Decimal]
    overtime_max_days_month: Optional[int]
    holiday_work_max_days: Optional[int]
    
    # 安全衛生
    safety_measures: Optional[str]
    
    # 苦情処理
    haken_moto_complaint_contact: Dict[str, Any]
    haken_saki_complaint_contact: Dict[str, Any]
    
    # 料金
    hourly_rate: Decimal
    overtime_rate: Decimal
    night_shift_rate: Optional[Decimal]
    holiday_rate: Optional[Decimal]
    
    # 福利厚生
    welfare_facilities: Optional[List[str]]
    
    # 責任者
    haken_moto_manager: Dict[str, Any]
    haken_saki_manager: Dict[str, Any]
    
    # 契約解除
    termination_measures: Optional[str]
    
    # その他
    is_kyotei_taisho: bool
    is_direct_hire_prevention: bool
    is_mukeiko_60over_only: bool
    
    # メタ
    number_of_workers: int
    status: str
    pdf_path: Optional[str]
    signed_date: Optional[date]
    notes: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    
    # Relaciones (opcional)
    employees: Optional[List[KobetsuEmployeeInfo]] = None

    class Config:
        from_attributes = True


class KobetsuKeiyakushoList(BaseModel):
    """個別契約書リスト用"""
    id: int
    contract_number: str
    worksite_name: str
    dispatch_start_date: date
    dispatch_end_date: date
    number_of_workers: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class KobetsuKeiyakushoStats(BaseModel):
    """個別契約書統計"""
    total_contracts: int
    active_contracts: int
    expiring_soon: int  # 30日以内に期限切れ
    expired_contracts: int
    draft_contracts: int
    total_workers: int
    
    class Config:
        from_attributes = True
