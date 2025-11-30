"""
Factory Schemas - Pydantic models for Factory API validation.

Includes schemas for cascading dropdowns:
派遣先 → 工場名 → 配属先 → ライン
"""
from datetime import date, time, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, validator


class ContractCycleTypeEnum(str, Enum):
    """Contract cycle type enumeration"""
    monthly = "monthly"
    annual = "annual"


class ContractCycleDayTypeEnum(str, Enum):
    """Contract cycle day type enumeration"""
    fixed = "fixed"
    month_end = "month_end"


# ========================================
# NESTED SCHEMAS
# ========================================

class SupervisorInfo(BaseModel):
    """指揮命令者情報"""
    department: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


class ResponsiblePersonInfo(BaseModel):
    """責任者情報"""
    department: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


class ComplaintHandlerInfo(BaseModel):
    """苦情処理担当者情報"""
    department: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


# ========================================
# FACTORY LINE SCHEMAS
# ========================================

class FactoryLineBase(BaseModel):
    """Base schema for factory line."""
    line_id: Optional[str] = None
    department: Optional[str] = Field(None, description="配属先")
    line_name: Optional[str] = Field(None, description="ライン名")
    supervisor_department: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_phone: Optional[str] = None
    job_description: Optional[str] = Field(None, description="仕事内容")
    job_description_detail: Optional[str] = None
    responsibility_level: str = Field(default="通常業務", description="責任の程度")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="時給単価")
    billing_rate: Optional[Decimal] = Field(None, ge=0, description="請求単価")
    overtime_rate: Optional[Decimal] = Field(None, ge=0)
    night_rate: Optional[Decimal] = Field(None, ge=0)
    holiday_rate: Optional[Decimal] = Field(None, ge=0)
    is_active: bool = True
    display_order: int = 0


class FactoryLineCreate(FactoryLineBase):
    """Schema for creating a factory line."""
    pass


class FactoryLineUpdate(BaseModel):
    """Schema for updating a factory line."""
    line_id: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None
    supervisor_department: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_phone: Optional[str] = None
    job_description: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None


class FactoryLineResponse(FactoryLineBase):
    """Response schema for factory line."""
    id: int
    factory_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# FACTORY SCHEMAS
# ========================================

class FactoryBase(BaseModel):
    """Base schema for factory."""
    # 派遣先情報
    company_name: str = Field(..., min_length=1, max_length=255, description="派遣先名")
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_fax: Optional[str] = None

    # 派遣先責任者
    client_responsible_department: Optional[str] = None
    client_responsible_name: Optional[str] = None
    client_responsible_phone: Optional[str] = None

    # 派遣先苦情処理担当者
    client_complaint_department: Optional[str] = None
    client_complaint_name: Optional[str] = None
    client_complaint_phone: Optional[str] = None

    # 工場情報
    plant_name: str = Field(..., min_length=1, max_length=255, description="工場名")
    plant_address: Optional[str] = None
    plant_phone: Optional[str] = None

    # 派遣元情報
    dispatch_responsible_department: Optional[str] = None
    dispatch_responsible_name: Optional[str] = None
    dispatch_responsible_phone: Optional[str] = None
    dispatch_complaint_department: Optional[str] = None
    dispatch_complaint_name: Optional[str] = None
    dispatch_complaint_phone: Optional[str] = None

    # スケジュール
    work_hours_description: Optional[str] = None
    break_time_description: Optional[str] = None
    calendar_description: Optional[str] = None
    day_shift_start: Optional[time] = None
    day_shift_end: Optional[time] = None
    night_shift_start: Optional[time] = None
    night_shift_end: Optional[time] = None
    break_minutes: int = Field(default=60, ge=0, le=180)

    # 時間外労働
    overtime_description: Optional[str] = None
    overtime_max_hours_day: Optional[Decimal] = Field(None, ge=0, le=24)
    overtime_max_hours_month: Optional[Decimal] = Field(None, ge=0, le=200)
    overtime_max_hours_year: Optional[int] = Field(None, ge=0, le=2000)

    # 休日労働
    holiday_work_description: Optional[str] = None
    holiday_work_max_days_month: Optional[int] = Field(None, ge=0, le=31)

    # 抵触日
    conflict_date: Optional[date] = Field(None, description="抵触日")

    # Contract cycle configuration
    contract_cycle_type: ContractCycleTypeEnum = Field(
        default=ContractCycleTypeEnum.annual,
        description="月次契約 or 年間契約"
    )
    cycle_day_type: ContractCycleDayTypeEnum = Field(
        default=ContractCycleDayTypeEnum.fixed,
        description="固定日 or 月末"
    )
    fiscal_year_end_month: int = Field(
        default=3,
        ge=1,
        le=12,
        description="決算月 (1-12)"
    )
    fiscal_year_end_day: int = Field(
        default=31,
        ge=1,
        le=31,
        description="決算日 (1-31)"
    )
    contract_renewal_days_before: int = Field(
        default=30,
        ge=0,
        le=365,
        description="更新通知日数"
    )

    # 支払条件
    closing_date: Optional[str] = None
    payment_date: Optional[str] = None
    bank_account: Optional[str] = None

    # 協定
    agreement_period: Optional[date] = None

    notes: Optional[str] = None

    @validator('fiscal_year_end_month')
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v

    @validator('fiscal_year_end_day')
    def validate_day(cls, v, values):
        if not 1 <= v <= 31:
            raise ValueError('Day must be between 1 and 31')
        # Additional validation for specific months could be added here
        month = values.get('fiscal_year_end_month')
        if month and month == 2 and v > 29:
            raise ValueError('February cannot have more than 29 days')
        if month and month in [4, 6, 9, 11] and v > 30:
            raise ValueError(f'Month {month} cannot have more than 30 days')
        return v

    @validator('contract_renewal_days_before')
    def validate_renewal_days(cls, v):
        if not 0 <= v <= 365:
            raise ValueError('Renewal days must be between 0 and 365')
        return v


class FactoryCreate(FactoryBase):
    """Schema for creating a factory."""
    factory_id: Optional[str] = None  # Auto-generated if not provided
    lines: Optional[List[FactoryLineCreate]] = []


class FactoryUpdate(BaseModel):
    """Schema for updating a factory."""
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    plant_name: Optional[str] = None
    plant_address: Optional[str] = None
    conflict_date: Optional[date] = None
    agreement_period: Optional[date] = None

    # Contract cycle configuration
    contract_cycle_type: Optional[ContractCycleTypeEnum] = None
    cycle_day_type: Optional[ContractCycleDayTypeEnum] = None
    fiscal_year_end_month: Optional[int] = Field(None, ge=1, le=12)
    fiscal_year_end_day: Optional[int] = Field(None, ge=1, le=31)
    contract_renewal_days_before: Optional[int] = Field(None, ge=0, le=365)

    is_active: Optional[bool] = None
    notes: Optional[str] = None


class FactoryResponse(FactoryBase):
    """Response schema for factory."""
    id: int
    factory_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[FactoryLineResponse] = []
    employees_count: int = 0

    class Config:
        from_attributes = True


class FactoryListItem(BaseModel):
    """List item schema for factory."""
    id: int
    factory_id: str
    company_name: str
    plant_name: str
    conflict_date: Optional[date] = None
    is_active: bool
    lines_count: int = 0
    employees_count: int = 0

    class Config:
        from_attributes = True


# ========================================
# DROPDOWN/CASCADE SCHEMAS
# ========================================

class CompanyOption(BaseModel):
    """Company option for dropdown."""
    company_name: str
    factories_count: int = 0


class PlantOption(BaseModel):
    """Plant option for dropdown (filtered by company)."""
    id: int
    factory_id: str
    plant_name: str
    plant_address: Optional[str] = None


class DepartmentOption(BaseModel):
    """Department option for dropdown (filtered by factory)."""
    department: str
    lines_count: int = 0


class LineOption(BaseModel):
    """Line option for dropdown (filtered by department)."""
    id: int
    line_id: Optional[str] = None
    line_name: str
    job_description: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    supervisor_name: Optional[str] = None


class FactoryCascadeData(BaseModel):
    """Complete cascade data for a selected line."""
    factory: FactoryResponse
    line: FactoryLineResponse


# ========================================
# IMPORT SCHEMA
# ========================================

class FactoryJSONImport(BaseModel):
    """Schema for importing factory from JSON file."""
    factory_id: str
    client_company: Dict[str, Any]
    plant: Dict[str, Any]
    lines: List[Dict[str, Any]]
    dispatch_company: Dict[str, Any]
    schedule: Dict[str, Any]
    payment: Dict[str, Any]
    agreement: Dict[str, Any]
