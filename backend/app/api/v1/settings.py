"""
Settings API Router - Company and system settings endpoints.

Provides read/write access to company (派遣元) information for contract generation.
Editable settings are stored in a JSON file.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.core.config import settings
from app.core.security import get_current_user

router = APIRouter()

# Settings file path for editable configuration
SETTINGS_FILE = Path("/app/data/uns_settings.json")


class CompanyInfo(BaseModel):
    """派遣元 company information."""
    name: str
    name_legal: str
    postal_code: str
    address: str
    full_address: str
    tel: str
    mobile: str
    fax: Optional[str] = None
    email: str
    website: str


class LicenseInfo(BaseModel):
    """Company licenses."""
    dispatch_license: str  # 労働者派遣事業
    support_org: str  # 登録支援機関
    job_placement: str  # 有料職業紹介事業


class ManagerInfo(BaseModel):
    """派遣元責任者 information."""
    name: str
    position: str


class ResponsiblePersonInfo(BaseModel):
    """派遣元責任者 (for contracts) information."""
    department: str
    position: str
    name: str
    phone: str


class ComplaintHandlerInfo(BaseModel):
    """派遣元苦情処理担当者 information."""
    department: str
    position: str
    name: str
    phone: str


class CompanySettings(BaseModel):
    """Full company settings response."""
    company: CompanyInfo
    licenses: LicenseInfo
    manager: ManagerInfo
    dispatch_responsible: ResponsiblePersonInfo
    complaint_handler: ComplaintHandlerInfo


@router.get("/company", response_model=CompanySettings)
async def get_company_settings():
    """
    Get 派遣元 (dispatch source company) information.

    This endpoint returns UNS-Kikaku company details used in contracts
    and official documents.
    """
    return CompanySettings(
        company=CompanyInfo(
            name=settings.COMPANY_NAME,
            name_legal=settings.COMPANY_NAME_LEGAL,
            postal_code=settings.COMPANY_POSTAL_CODE,
            address=settings.COMPANY_ADDRESS,
            full_address=f"〒{settings.COMPANY_POSTAL_CODE} {settings.COMPANY_ADDRESS}",
            tel=settings.COMPANY_TEL,
            mobile=settings.COMPANY_MOBILE,
            fax=settings.COMPANY_FAX or "",
            email=settings.COMPANY_EMAIL,
            website=settings.COMPANY_WEBSITE,
        ),
        licenses=LicenseInfo(
            dispatch_license=settings.COMPANY_LICENSE_NUMBER,
            support_org=settings.COMPANY_SUPPORT_ORG_NUMBER,
            job_placement=settings.COMPANY_JOB_PLACEMENT_NUMBER,
        ),
        manager=ManagerInfo(
            name=settings.DISPATCH_MANAGER_NAME,
            position=settings.DISPATCH_MANAGER_POSITION,
        ),
        dispatch_responsible=ResponsiblePersonInfo(
            department=settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
            position=settings.DISPATCH_RESPONSIBLE_POSITION,
            name=settings.DISPATCH_RESPONSIBLE_NAME,
            phone=settings.DISPATCH_RESPONSIBLE_PHONE,
        ),
        complaint_handler=ComplaintHandlerInfo(
            department=settings.DISPATCH_COMPLAINT_DEPARTMENT,
            position=settings.DISPATCH_COMPLAINT_POSITION,
            name=settings.DISPATCH_COMPLAINT_NAME,
            phone=settings.DISPATCH_COMPLAINT_PHONE,
        ),
    )


@router.get("/system")
async def get_system_info():
    """Get basic system information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


# ========================================
# EDITABLE SETTINGS (stored in JSON file)
# ========================================

class ContactInfoEditable(BaseModel):
    """連絡先情報 (編集可能)"""
    department: str = Field(default="", max_length=100, description="部署名")
    position: str = Field(default="", max_length=100, description="役職")
    name: str = Field(default="", max_length=100, description="氏名")
    phone: str = Field(default="", max_length=20, description="電話番号")


class ManagerInfoEditable(ContactInfoEditable):
    """責任者情報 (編集可能)"""
    license_number: Optional[str] = Field(default="", max_length=50, description="講習修了証番号")


class DefaultWorkConditions(BaseModel):
    """デフォルト就業条件"""
    work_days: list = Field(default=["月", "火", "水", "木", "金"])
    work_start_time: str = Field(default="08:00")
    work_end_time: str = Field(default="17:00")
    break_time_minutes: int = Field(default=60, ge=0, le=180)
    hourly_rate: int = Field(default=1500, ge=800, le=10000)
    overtime_rate: int = Field(default=1875, ge=1000, le=15000)
    responsibility_level: str = Field(default="通常業務")


class UNSFormDefaults(BaseModel):
    """
    契約書フォームで使用するUNS企画のデフォルト値
    フロントエンドの config/uns-defaults.ts に相当
    """
    # 派遣元苦情処理担当者
    complaint_contact: ContactInfoEditable = Field(
        default_factory=lambda: ContactInfoEditable(
            department="管理部",
            position="部長",
            name="",
            phone=""
        )
    )

    # 派遣元責任者
    manager: ManagerInfoEditable = Field(
        default_factory=lambda: ManagerInfoEditable(
            department="派遣事業部",
            position="部長",
            name="",
            phone="",
            license_number=""
        )
    )

    # デフォルト就業条件
    work_conditions: DefaultWorkConditions = Field(default_factory=DefaultWorkConditions)


def ensure_settings_dir():
    """Ensure the settings directory exists."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_form_defaults() -> UNSFormDefaults:
    """Load form defaults from JSON file, or return defaults."""
    ensure_settings_dir()

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return UNSFormDefaults(**data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading settings: {e}")

    return UNSFormDefaults()


def save_form_defaults(defaults: UNSFormDefaults) -> None:
    """Save form defaults to JSON file."""
    ensure_settings_dir()

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(defaults.model_dump(), f, ensure_ascii=False, indent=2)


@router.get("/form-defaults", response_model=UNSFormDefaults)
async def get_form_defaults():
    """
    Get UNS company defaults for contract forms.

    Returns the default values for 派遣元苦情処理担当者, 派遣元責任者,
    and default work conditions used when creating new contracts.
    """
    return load_form_defaults()


@router.put("/form-defaults", response_model=UNSFormDefaults)
async def update_form_defaults(defaults: UNSFormDefaults, current_user: dict = Depends(get_current_user)):
    """
    Update UNS company defaults for contract forms.

    Updates the default values that will be pre-filled when creating new contracts.
    """
    try:
        save_form_defaults(defaults)
        return defaults
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定の保存に失敗しました: {str(e)}"
        )
