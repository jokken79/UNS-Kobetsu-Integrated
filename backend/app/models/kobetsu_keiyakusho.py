# backend/app/models/kobetsu_keiyakusho.py
"""
個別契約書 (Kobetsu Keiyakusho) Models
Labor Dispatch Individual Contract models
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, Numeric, Boolean,
    DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class KobetsuKeiyakusho(Base):
    """
    個別契約書 - Individual Dispatch Contract
    
    Esta tabla almacena los contratos individuales de dispatch
    según la 労働者派遣法第26条 (Labor Dispatch Law Article 26)
    """
    __tablename__ = "kobetsu_keiyakusho"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ========================================
    # RELACIONES
    # ========================================
    factory_id = Column(Integer, ForeignKey('factories.id', ondelete='CASCADE'), nullable=False, index=True)
    dispatch_assignment_id = Column(Integer, ForeignKey('dispatch_assignments.id', ondelete='SET NULL'), nullable=True)

    # New: Base Madre references (added in migration 002)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True, index=True)
    plant_id = Column(Integer, ForeignKey('plants.plant_id', ondelete='SET NULL'), nullable=True, index=True)

    # Contract renewal tracking (added in migration 004)
    previous_contract_id = Column(Integer, ForeignKey('kobetsu_keiyakusho.id', ondelete='SET NULL'), nullable=True, index=True)

    # ========================================
    # 基本情報 (Información Básica)
    # ========================================
    contract_number = Column(String(50), unique=True, nullable=False, index=True)
    contract_date = Column(Date, nullable=False)  # Fecha de firma
    dispatch_start_date = Column(Date, nullable=False, index=True)
    dispatch_end_date = Column(Date, nullable=False, index=True)
    
    # ========================================
    # Item 1: 業務内容 (Contenido del trabajo)
    # ========================================
    work_content = Column(Text, nullable=False)
    
    # ========================================
    # Item 2: 責任の程度 (Nivel de responsabilidad)
    # ========================================
    responsibility_level = Column(String(50), nullable=False)
    # Valores: "補助的業務", "通常業務", "責任業務"
    
    # ========================================
    # Item 3: 派遣先事業所 (Lugar de trabajo)
    # ========================================
    worksite_name = Column(String(255), nullable=False)
    worksite_address = Column(Text, nullable=False)
    organizational_unit = Column(String(100), nullable=True)  # 組織単位
    
    # ========================================
    # Item 4: 指揮命令者 (Supervisor)
    # ========================================
    supervisor_department = Column(String(100), nullable=False)
    supervisor_position = Column(String(100), nullable=False)
    supervisor_name = Column(String(100), nullable=False)
    
    # ========================================
    # Items 5-6: 就業条件 (Condiciones laborales)
    # ========================================
    work_days = Column(JSONB, nullable=False)
    # Ejemplo: ["月", "火", "水", "木", "金"]
    work_start_time = Column(Time, nullable=False)
    work_end_time = Column(Time, nullable=False)
    break_time_minutes = Column(Integer, nullable=False)
    
    # ========================================
    # Item 12: 時間外労働 (Horas extra)
    # ========================================
    overtime_max_hours_day = Column(Numeric(4, 2), nullable=True)
    overtime_max_hours_month = Column(Numeric(5, 2), nullable=True)
    overtime_max_days_month = Column(Integer, nullable=True)
    holiday_work_max_days = Column(Integer, nullable=True)
    
    # ========================================
    # Item 7: 安全衛生 (Seguridad e higiene)
    # ========================================
    safety_measures = Column(Text, nullable=True)
    
    # ========================================
    # Item 8: 苦情処理 (Manejo de quejas)
    # ========================================
    haken_moto_complaint_contact = Column(JSONB, nullable=False)
    # {"department": "総務部", "position": "部長", "name": "山田太郎", "phone": "052-123-4567"}
    haken_saki_complaint_contact = Column(JSONB, nullable=False)
    
    # ========================================
    # 派遣料金 (Tarifas)
    # ========================================
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    overtime_rate = Column(Numeric(10, 2), nullable=False)
    night_shift_rate = Column(Numeric(10, 2), nullable=True)
    holiday_rate = Column(Numeric(10, 2), nullable=True)
    
    # ========================================
    # Item 13: 福利厚生 (Bienestar)
    # ========================================
    welfare_facilities = Column(JSONB, nullable=True)
    # Ejemplo: ["食堂", "更衣室", "休憩室", "駐車場"]
    
    # ========================================
    # Items 10-11: 責任者 (Responsables)
    # ========================================
    haken_moto_manager = Column(JSONB, nullable=False)
    # {"department": "派遣事業部", "position": "部長", "name": "鈴木一郎", "phone": "052-999-8888"}
    haken_saki_manager = Column(JSONB, nullable=False)
    
    # ========================================
    # Item 9: 契約解除時の措置 (Medidas de terminación)
    # ========================================
    termination_measures = Column(Text, nullable=True)
    
    # ========================================
    # Items 14-16: その他法定事項 (Otros requisitos legales)
    # ========================================
    is_kyotei_taisho = Column(Boolean, default=False)  # Item 15: 労使協定方式
    is_direct_hire_prevention = Column(Boolean, default=False)  # Item 14
    is_mukeiko_60over_only = Column(Boolean, default=False)  # Item 16
    
    # ========================================
    # 派遣人数 (Número de trabajadores)
    # ========================================
    number_of_workers = Column(Integer, nullable=False)
    
    # ========================================
    # STATUS Y METADATA
    # ========================================
    status = Column(String(20), nullable=False, default='draft')
    # Valores: draft, active, expired, cancelled, renewed
    pdf_path = Column(String(500), nullable=True)
    signed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # ========================================
    # TIMESTAMPS
    # ========================================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # ========================================
    # RELATIONSHIPS
    # ========================================
    factory = relationship("Factory", back_populates="kobetsu_contracts")
    dispatch_assignment = relationship("DispatchAssignment", back_populates="kobetsu_contracts")
    employees = relationship("KobetsuEmployee", back_populates="kobetsu_keiyakusho", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    # New: Base Madre relationships
    company = relationship("Company", back_populates="kobetsu_contracts")
    plant = relationship("Plant", back_populates="kobetsu_contracts")

    # Self-referential relationship for contract renewal chains
    previous_contract = relationship("KobetsuKeiyakusho", remote_side=[id], foreign_keys=[previous_contract_id])
    
    # ========================================
    # TABLE CONSTRAINTS
    # ========================================
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'expired', 'cancelled', 'renewed')",
            name='ck_kobetsu_status'
        ),
        CheckConstraint(
            'dispatch_start_date <= dispatch_end_date',
            name='ck_kobetsu_dates'
        ),
        CheckConstraint(
            'number_of_workers > 0',
            name='ck_kobetsu_workers'
        ),
        Index('ix_kobetsu_factory_id', 'factory_id'),
        Index('ix_kobetsu_status', 'status'),
        Index('ix_kobetsu_dispatch_dates', 'dispatch_start_date', 'dispatch_end_date'),
    )
    
    def __repr__(self):
        return f"<KobetsuKeiyakusho(id={self.id}, contract_number='{self.contract_number}', factory='{self.worksite_name}')>"


class KobetsuEmployee(Base):
    """
    個別契約書に紐づく従業員
    Employees associated with a Kobetsu Keiyakusho

    重要: 同じラインでも、各従業員の単価が異なる場合があります。
    そのため、契約レベルの単価とは別に、従業員ごとの単価を保存します。

    Nota: No se almacenan nombres en el contrato según la ley,
    pero sí se mantiene la relación para gestión interna
    """
    __tablename__ = "kobetsu_employees"

    id = Column(Integer, primary_key=True, index=True)
    kobetsu_keiyakusho_id = Column(
        Integer,
        ForeignKey('kobetsu_keiyakusho.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    employee_id = Column(
        Integer,
        ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # ========================================
    # 個別単価 (Individual Rates per Employee)
    # ========================================
    # これらは契約レベルの単価をオーバーライドします
    hourly_rate = Column(Numeric(10, 2), nullable=True)  # 時給単価
    overtime_rate = Column(Numeric(10, 2), nullable=True)  # 時間外単価
    night_shift_rate = Column(Numeric(10, 2), nullable=True)  # 深夜単価
    holiday_rate = Column(Numeric(10, 2), nullable=True)  # 休日単価
    billing_rate = Column(Numeric(10, 2), nullable=True)  # 請求単価

    # ========================================
    # 派遣期間 (Individual Dispatch Period)
    # ========================================
    # 途中入社や途中退社の場合、契約期間と異なる場合があります
    individual_start_date = Column(Date, nullable=True)  # 個別開始日
    individual_end_date = Column(Date, nullable=True)  # 個別終了日

    # ========================================
    # 雇用形態 (Employment Type - for PDF)
    # ========================================
    is_indefinite_employment = Column(Boolean, default=False)  # 無期雇用

    # ========================================
    # メタデータ
    # ========================================
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    kobetsu_keiyakusho = relationship("KobetsuKeiyakusho", back_populates="employees")
    employee = relationship("Employee", back_populates="contracts")
    
    __table_args__ = (
        UniqueConstraint('kobetsu_keiyakusho_id', 'employee_id', name='uq_kobetsu_employee'),
        Index('ix_kobetsu_employees_kobetsu_id', 'kobetsu_keiyakusho_id'),
        Index('ix_kobetsu_employees_employee_id', 'employee_id'),
    )
    
    def __repr__(self):
        return f"<KobetsuEmployee(kobetsu_id={self.kobetsu_keiyakusho_id}, employee_id={self.employee_id})>"
