"""
Application configuration settings.
Loads environment variables and provides typed access to configuration.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "UNS Kobetsu Keiyakusho"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database - supports both direct URL and individual components
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "uns_user"
    POSTGRES_PASSWORD: str = "uns_password"
    POSTGRES_DB: str = "uns_kobetsu"

    def get_database_url(self) -> str:
        """Get database URL, preferring direct URL if set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_database_url_async(self) -> str:
        """Get async database URL."""
        base_url = self.get_database_url()
        return base_url.replace("postgresql://", "postgresql+asyncpg://")

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # JWT Authentication
    JWT_SECRET_KEY: str = "uns-kobetsu-local-dev-secret-key-2024-do-not-use-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3010", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # UNS Kikaku Company Information (派遣元)
    COMPANY_NAME: str = "ユニバーサル企画株式会社"
    COMPANY_NAME_LEGAL: str = "ユニバーサル企画 株式会社"
    COMPANY_POSTAL_CODE: str = "461-0025"
    COMPANY_ADDRESS: str = "愛知県名古屋市東区徳川2-18-18"
    COMPANY_TEL: str = "052-938-8840"
    COMPANY_MOBILE: str = "080-7376-1988"
    COMPANY_FAX: str = ""
    COMPANY_EMAIL: str = "infoapp@uns-kikaku.com"
    COMPANY_WEBSITE: str = "www.uns-kikaku.com"

    # 許可証番号
    COMPANY_LICENSE_NUMBER: str = "派 23-303669"  # 労働者派遣事業
    COMPANY_SUPPORT_ORG_NUMBER: str = "21登-006367"  # 登録支援機関
    COMPANY_JOB_PLACEMENT_NUMBER: str = "23-ユ-302989"  # 有料職業紹介事業

    # 派遣元責任者 (Dispatch Company Manager)
    DISPATCH_MANAGER_NAME: str = "中山 雅和"
    DISPATCH_MANAGER_POSITION: str = "代表取締役"

    # 派遣元責任者 (Dispatch Responsible Person - for contracts)
    DISPATCH_RESPONSIBLE_DEPARTMENT: str = "営業部"
    DISPATCH_RESPONSIBLE_POSITION: str = "取締役 部長"
    DISPATCH_RESPONSIBLE_NAME: str = "中山 欣英"
    DISPATCH_RESPONSIBLE_PHONE: str = "052-938-8840"

    # 派遣元苦情処理担当者 (Complaint Handler)
    DISPATCH_COMPLAINT_DEPARTMENT: str = "営業部"
    DISPATCH_COMPLAINT_POSITION: str = "取締役 部長"
    DISPATCH_COMPLAINT_NAME: str = "中山 欣英"
    DISPATCH_COMPLAINT_PHONE: str = "052-938-8840"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Document Generation
    PDF_TEMPLATE_DIR: str = "./templates/pdf"
    PDF_OUTPUT_DIR: str = "./outputs/pdf"  # Maps to uns_kobetsu_outputs volume
    EXCEL_TEMPLATE_DIR: str = "./templates/excel"  # Excel templates for document generation
    DEFAULT_DOCUMENT_FORMAT: str = "xlsx"  # Default output format: xlsx or pdf

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
