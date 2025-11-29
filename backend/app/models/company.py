"""
Company model - matches Base Madre schema

This model represents client companies (派遣先企業) and is designed to sync
with Base Madre's companies table.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    """
    Company (派遣先企業)

    Represents a client company that hires dispatch workers.
    Synced from Base Madre API.
    """
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_kana = Column(String(255))
    address = Column(Text)
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # Responsible person
    responsible_department = Column(String(100))
    responsible_name = Column(String(100))
    responsible_phone = Column(String(50))

    # Contract period
    contract_start = Column(Date)
    contract_end = Column(Date)

    # Metadata
    notes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Base Madre sync tracking
    base_madre_company_id = Column(Integer, unique=True, index=True, comment="Reference to Base Madre company_id")
    last_synced_at = Column(DateTime, comment="Last sync from Base Madre")

    # Relationships
    jigyosho = relationship("Jigyosho", back_populates="company", cascade="all, delete-orphan")
    plants = relationship("Plant", back_populates="company", cascade="all, delete-orphan")
    kobetsu_contracts = relationship("KobetsuKeiyakusho", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.company_id}, name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "company_id": self.company_id,
            "name": self.name,
            "name_kana": self.name_kana,
            "address": self.address,
            "phone": self.phone,
            "fax": self.fax,
            "email": self.email,
            "website": self.website,
            "responsible_department": self.responsible_department,
            "responsible_name": self.responsible_name,
            "responsible_phone": self.responsible_phone,
            "contract_start": self.contract_start.isoformat() if self.contract_start else None,
            "contract_end": self.contract_end.isoformat() if self.contract_end else None,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "base_madre_company_id": self.base_madre_company_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
        }
