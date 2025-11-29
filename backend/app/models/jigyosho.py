"""
Jigyosho (Regional Office) model - matches Base Madre schema

事業所 (Regional offices) are organizational units within a company.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Jigyosho(Base):
    """
    Jigyosho (事業所 - Regional Office)

    Represents a regional office or business unit within a company.
    Synced from Base Madre API.
    """
    __tablename__ = "jigyosho"

    jigyosho_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False, index=True)

    jigyosho_name = Column(String(255), nullable=False)
    jigyosho_code = Column(String(50))
    jigyosho_address = Column(Text)
    jigyosho_phone = Column(String(50))
    jigyosho_fax = Column(String(50))

    manager_name = Column(String(100))
    manager_phone = Column(String(50))

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Base Madre sync tracking
    base_madre_jigyosho_id = Column(Integer, unique=True, index=True)
    last_synced_at = Column(DateTime)

    # Relationships
    company = relationship("Company", back_populates="jigyosho")
    plants = relationship("Plant", back_populates="jigyosho")

    def __repr__(self):
        return f"<Jigyosho(id={self.jigyosho_id}, name='{self.jigyosho_name}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "jigyosho_id": self.jigyosho_id,
            "company_id": self.company_id,
            "jigyosho_name": self.jigyosho_name,
            "jigyosho_code": self.jigyosho_code,
            "jigyosho_address": self.jigyosho_address,
            "jigyosho_phone": self.jigyosho_phone,
            "jigyosho_fax": self.jigyosho_fax,
            "manager_name": self.manager_name,
            "manager_phone": self.manager_phone,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "base_madre_jigyosho_id": self.base_madre_jigyosho_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
        }
