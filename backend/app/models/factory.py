"""
Factory Model - 派遣先/工場 (Dispatch Destination/Factory)

Matches the JSON structure from UNS-ClaudeJP-6.0.0 config/factories/
Contains all information needed for 個別契約書 generation.
"""
from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, Time,
    DateTime, Numeric, ForeignKey, JSON, Index, UniqueConstraint,
    CheckConstraint, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class ContractCycleType(str, PyEnum):
    """Contract cycle type enumeration"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class ContractCycleDayType(str, PyEnum):
    """Contract cycle day type enumeration"""
    FIXED = "fixed"
    MONTH_END = "month_end"


class Factory(Base):
    """
    派遣先/工場 - Client company and factory information.

    Structure matches config/factories/*.json from UNS-ClaudeJP-6.0.0
    """
    __tablename__ = "factories"

    id = Column(Integer, primary_key=True, index=True)

    # Unique identifier: "会社名__工場名"
    factory_id = Column(String(200), unique=True, nullable=False, index=True)

    # ========================================
    # 派遣先情報 (Client Company)
    # ========================================
    company_name = Column(String(255), nullable=False, index=True)  # 派遣先名
    company_address = Column(Text)  # 派遣先住所
    company_phone = Column(String(50))  # 派遣先電話
    company_fax = Column(String(50))  # 派遣先FAX

    # 派遣先責任者
    client_responsible_department = Column(String(100))
    client_responsible_position = Column(String(100))  # 役職: 課長, 部長, etc.
    client_responsible_name = Column(String(100))
    client_responsible_phone = Column(String(50))

    # 派遣先苦情処理担当者
    client_complaint_department = Column(String(100))
    client_complaint_position = Column(String(100))  # 役職: 担当者, 課長, etc.
    client_complaint_name = Column(String(100))
    client_complaint_phone = Column(String(50))

    # ========================================
    # 工場情報 (Plant)
    # ========================================
    plant_name = Column(String(255), nullable=False, index=True)  # 工場名
    plant_address = Column(Text)  # 工場住所
    plant_phone = Column(String(50))  # 工場電話

    # ========================================
    # 派遣元情報 (Dispatch Company - UNS)
    # ========================================
    dispatch_responsible_department = Column(String(100))
    dispatch_responsible_name = Column(String(100))
    dispatch_responsible_phone = Column(String(50))

    dispatch_complaint_department = Column(String(100))
    dispatch_complaint_name = Column(String(100))
    dispatch_complaint_phone = Column(String(50))

    # ========================================
    # スケジュール (Schedule)
    # ========================================
    work_hours_description = Column(Text)  # 就業時間 (text description)
    break_time_description = Column(Text)  # 休憩時間 (text description)
    calendar_description = Column(Text)  # カレンダー説明

    # Parsed times for calculations
    day_shift_start = Column(Time)
    day_shift_end = Column(Time)
    night_shift_start = Column(Time)
    night_shift_end = Column(Time)
    break_minutes = Column(Integer, default=60)

    # 時間外労働
    overtime_description = Column(Text)
    overtime_max_hours_day = Column(Numeric(4, 2))
    overtime_max_hours_month = Column(Numeric(5, 2))
    overtime_max_hours_year = Column(Integer)
    overtime_special_max_month = Column(Numeric(5, 2))  # 特別条項
    overtime_special_count_year = Column(Integer)  # 年間回数

    # 休日労働
    holiday_work_description = Column(Text)
    holiday_work_max_days_month = Column(Integer)

    # 抵触日 (Contract limit date - very important!)
    conflict_date = Column(Date, index=True)  # 抵触日

    # 契約期間 (Contract period)
    contract_start_date = Column(Date, index=True)  # 契約開始日
    contract_end_date = Column(Date, index=True)  # 契約終了日

    # ========================================
    # Contract Cycle Configuration
    # ========================================
    contract_cycle_type = Column(
        Enum('monthly', 'annual', name='contract_cycle_type', create_type=False),
        nullable=False,
        default='annual',
        comment="月次契約 or 年間契約"
    )
    cycle_day_type = Column(
        Enum('fixed', 'month_end', name='contract_cycle_day_type', create_type=False),
        nullable=False,
        default='fixed',
        comment="固定日 or 月末"
    )
    fiscal_year_end_month = Column(
        Integer,
        nullable=False,
        default=3,
        comment="決算月 (1-12)"
    )
    fiscal_year_end_day = Column(
        Integer,
        nullable=False,
        default=31,
        comment="決算日 (1-31)"
    )
    contract_renewal_days_before = Column(
        Integer,
        nullable=False,
        default=30,
        comment="自動更新通知日数"
    )

    # Time unit for calculations (e.g., 15 minutes)
    time_unit_minutes = Column(Numeric(4, 1), default=15)

    # ========================================
    # 支払条件 (Payment Terms)
    # ========================================
    closing_date = Column(String(50))  # 締め日 (e.g., "月末日", "20日")
    payment_date = Column(String(50))  # 支払日 (e.g., "翌月末日")
    bank_account = Column(Text)  # 振込先

    worker_closing_date = Column(String(50))  # 労働者締め日
    worker_payment_date = Column(String(50))  # 労働者支払日
    worker_calendar = Column(Text)  # 労働者カレンダー

    # ========================================
    # 協定 (Agreement)
    # ========================================
    agreement_period = Column(Date)  # 当該協定期間
    agreement_explainer = Column(String(255))  # 説明者

    # ========================================
    # メタデータ
    # ========================================
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ========================================
    # Relationships
    # ========================================
    lines = relationship("FactoryLine", back_populates="factory", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="factory")
    kobetsu_contracts = relationship("KobetsuKeiyakusho", back_populates="factory")

    __table_args__ = (
        Index('ix_factories_company_plant', 'company_name', 'plant_name'),
        CheckConstraint('fiscal_year_end_month BETWEEN 1 AND 12',
                       name='ck_fiscal_month'),
        CheckConstraint('fiscal_year_end_day BETWEEN 1 AND 31',
                       name='ck_fiscal_day'),
        CheckConstraint('contract_renewal_days_before BETWEEN 0 AND 365',
                       name='ck_renewal_days'),
    )

    def __repr__(self):
        return f"<Factory {self.factory_id}>"


class FactoryLine(Base):
    """
    配属先/ライン - Department and production line within a factory.

    Each factory can have multiple lines with different:
    - 配属先 (department)
    - ライン (line name)
    - 仕事内容 (job description)
    - 時給単価 (hourly rate)
    - 指揮命令者 (supervisor)
    """
    __tablename__ = "factory_lines"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="CASCADE"), nullable=False)

    # Line identifier (e.g., "Factory-10")
    line_id = Column(String(50), index=True)

    # ========================================
    # 配属先情報 (Assignment)
    # ========================================
    department = Column(String(100))  # 配属先 (e.g., "製造部")
    line_name = Column(String(100))  # ライン名 (e.g., "製造1課", "Aライン")

    # 指揮命令者 (Supervisor)
    supervisor_department = Column(String(100))
    supervisor_position = Column(String(100))  # 役職: 課長, 部長, リーダー, etc.
    supervisor_name = Column(String(100))
    supervisor_phone = Column(String(50))

    # ========================================
    # 業務内容 (Job Details)
    # ========================================
    job_description = Column(Text)  # 仕事内容
    job_description_detail = Column(Text)  # 仕事内容詳細
    responsibility_level = Column(String(50), default="通常業務")  # 責任の程度

    # ========================================
    # 料金 (Rates)
    # ========================================
    hourly_rate = Column(Numeric(8, 2))  # 時給単価
    billing_rate = Column(Numeric(8, 2))  # 請求単価
    overtime_rate = Column(Numeric(8, 2))  # 時間外単価
    night_rate = Column(Numeric(8, 2))  # 深夜単価
    holiday_rate = Column(Numeric(8, 2))  # 休日単価

    # ========================================
    # メタデータ
    # ========================================
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)  # For sorting in dropdowns

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    factory = relationship("Factory", back_populates="lines")
    employees = relationship("Employee", back_populates="factory_line")

    __table_args__ = (
        UniqueConstraint('factory_id', 'line_id', name='uq_factory_line'),
        Index('ix_factory_lines_factory', 'factory_id'),
    )

    def __repr__(self):
        return f"<FactoryLine {self.factory_id}:{self.line_name}>"
