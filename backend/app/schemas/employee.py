"""
Employee Schemas - Pydantic models for Employee API validation.

Based on DBGenzai structure from Excel.
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, EmailStr


# ========================================
# BASE SCHEMA
# ========================================

class EmployeeBase(BaseModel):
    """Base schema for employee."""
    # 基本情報
    full_name_kanji: str = Field(..., min_length=1, max_length=100, description="氏名")
    full_name_kana: str = Field(..., min_length=1, max_length=100, description="カナ")
    full_name_romaji: Optional[str] = Field(None, max_length=100, description="ローマ字")

    gender: Optional[str] = Field(None, description="性別")
    date_of_birth: Optional[date] = Field(None, description="生年月日")
    nationality: str = Field(default="ベトナム", description="国籍")

    # 連絡先
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    # 緊急連絡先
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    # 雇用情報
    hire_date: date = Field(..., description="入社日")
    contract_type: Optional[str] = Field(None, description="契約種類")
    employment_type: Optional[str] = Field(None, description="雇用形態")
    position: Optional[str] = Field(None, description="職種")

    # 給与
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="時給")
    billing_rate: Optional[Decimal] = Field(None, ge=0, description="請求単価")
    transportation_allowance: Optional[Decimal] = Field(default=0, ge=0, description="交通費")

    # 在留資格
    visa_type: Optional[str] = None
    visa_expiry_date: Optional[date] = Field(None, description="ビザ期限")
    zairyu_card_number: Optional[str] = None
    passport_number: Optional[str] = None

    # 保険
    has_employment_insurance: bool = Field(default=True, description="雇用保険")
    has_health_insurance: bool = Field(default=True, description="健康保険")
    has_pension_insurance: bool = Field(default=True, description="厚生年金")

    # 銀行
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_type: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_holder: Optional[str] = None

    notes: Optional[str] = None


# ========================================
# CREATE SCHEMA
# ========================================

class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""
    employee_number: str = Field(..., min_length=1, max_length=20, description="社員№")
    hakenmoto_id: Optional[str] = None
    rirekisho_id: Optional[str] = None

    # 派遣先 (can be set later)
    factory_id: Optional[int] = None
    factory_line_id: Optional[int] = None
    company_name: Optional[str] = None
    plant_name: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None

    @field_validator('employee_number')
    @classmethod
    def validate_employee_number(cls, v):
        if not v or not v.strip():
            raise ValueError('社員番号は必須です')
        return v.strip()


# ========================================
# UPDATE SCHEMA
# ========================================

class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    full_name_kanji: Optional[str] = None
    full_name_kana: Optional[str] = None
    full_name_romaji: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

    address: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    factory_id: Optional[int] = None
    factory_line_id: Optional[int] = None
    company_name: Optional[str] = None
    plant_name: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None
    position: Optional[str] = None

    hourly_rate: Optional[Decimal] = None
    billing_rate: Optional[Decimal] = None

    visa_expiry_date: Optional[date] = None
    zairyu_card_number: Optional[str] = None

    status: Optional[str] = None
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None

    notes: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed = ["active", "resigned", "on_leave", "transferred"]
            if v not in allowed:
                raise ValueError(f'status must be one of: {allowed}')
        return v


# ========================================
# RESPONSE SCHEMAS
# ========================================

class EmployeeResponse(EmployeeBase):
    """Response schema for employee."""
    id: int
    employee_number: str
    hakenmoto_id: Optional[str] = None
    rirekisho_id: Optional[str] = None

    factory_id: Optional[int] = None
    factory_line_id: Optional[int] = None
    company_name: Optional[str] = None
    plant_name: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None

    status: str
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None

    # 有給
    yukyu_total: int = 0
    yukyu_used: int = 0
    yukyu_remaining: int = 0

    # 住居
    apartment_name: Optional[str] = None
    apartment_room: Optional[str] = None
    apartment_rent: Optional[Decimal] = None
    is_corporate_housing: bool = False

    # Calculated
    age: Optional[int] = None
    display_name: str = ""  # 日本人→漢字, 外国人→カタカナ
    is_indefinite_employment: bool = False
    employment_type_display: str = "□無期雇用  ☑有期雇用"
    age_category: str = ""  # 年齢区分 for 派遣先通知書

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeListItem(BaseModel):
    """List item schema for employee."""
    id: int
    employee_number: str
    full_name_kanji: str
    full_name_kana: str
    company_name: Optional[str] = None
    plant_name: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None
    position: Optional[str] = None
    hire_date: date
    hourly_rate: Optional[Decimal] = None  # 時給 (lo que pagamos al empleado)
    billing_rate: Optional[Decimal] = None  # 単価 (lo que la fábrica nos paga)
    status: str
    nationality: str = "ベトナム"
    visa_expiry_date: Optional[date] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator('age', mode='before')
    @classmethod
    def calculate_age_from_dob(cls, v, info):
        """Calculate age from date_of_birth, overriding stored age."""
        data = info.data
        if 'date_of_birth' in data and data['date_of_birth'] is not None:
            dob = data['date_of_birth']
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        # If no date_of_birth, keep whatever value (likely None)
        return v


class EmployeeStats(BaseModel):
    """Statistics for employees."""
    total_employees: int
    active_employees: int
    resigned_employees: int
    visa_expiring_soon: int  # 30 days
    average_age: Optional[float] = None
    under_18_count: int = 0
    over_60_count: int = 0
    by_company: List[dict] = []
    by_nationality: List[dict] = []


# ========================================
# ASSIGNMENT SCHEMA
# ========================================

class EmployeeAssignment(BaseModel):
    """Schema for assigning employee to factory/line."""
    factory_id: int
    factory_line_id: Optional[int] = None
    company_name: Optional[str] = None
    plant_name: Optional[str] = None
    department: Optional[str] = None
    line_name: Optional[str] = None
    position: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    billing_rate: Optional[Decimal] = None
    start_date: Optional[date] = None


# ========================================
# IMPORT/EXPORT SCHEMAS
# ========================================

class EmployeeExcelImport(BaseModel):
    """Schema for importing employee from Excel."""
    現在: Optional[str] = None  # 在籍/退社
    社員番号: str
    派遣先: Optional[str] = None
    配属先: Optional[str] = None
    氏名: str
    カナ: str
    時給: Optional[float] = None
    請求単価: Optional[float] = None
    入社日: Optional[str] = None
    退社日: Optional[str] = None
    ビザ期限: Optional[str] = None
    国籍: Optional[str] = None


class EmployeeForContract(BaseModel):
    """Minimal employee info for contract selection."""
    id: int
    employee_number: str
    full_name_kanji: str
    full_name_kana: str
    display_name: str = ""  # 日本人→漢字, 外国人→カタカナ
    gender: Optional[str] = None
    age: Optional[int] = None
    age_category: str = ""  # 年齢区分 for 派遣先通知書
    nationality: str = "ベトナム"
    has_employment_insurance: bool = True
    has_health_insurance: bool = True
    has_pension_insurance: bool = True
    is_indefinite_employment: bool = False

    class Config:
        from_attributes = True
