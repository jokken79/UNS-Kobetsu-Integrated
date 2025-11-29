"""
Plant model - matches Base Madre schema

Plants (工場) are physical locations where workers are dispatched.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Plant(Base):
    """
    Plant (工場)

    Represents a plant/factory location within a company.
    Synced from Base Madre API.
    """
    __tablename__ = "plants"

    plant_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False, index=True)
    jigyosho_id = Column(Integer, ForeignKey('jigyosho.jigyosho_id', ondelete='SET NULL'), index=True)

    plant_name = Column(String(255), nullable=False, index=True)
    plant_code = Column(String(50))
    plant_address = Column(Text)
    plant_phone = Column(String(50))

    manager_name = Column(String(100))
    capacity = Column(Integer)  # Number of workers capacity

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Base Madre sync tracking
    base_madre_plant_id = Column(Integer, unique=True, index=True, comment="Reference to Base Madre plant_id")
    last_synced_at = Column(DateTime, comment="Last sync from Base Madre")

    # Relationships
    company = relationship("Company", back_populates="plants")
    jigyosho = relationship("Jigyosho", back_populates="plants")
    kobetsu_contracts = relationship("KobetsuKeiyakusho", back_populates="plant")

    def __repr__(self):
        return f"<Plant(id={self.plant_id}, name='{self.plant_name}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "plant_id": self.plant_id,
            "company_id": self.company_id,
            "jigyosho_id": self.jigyosho_id,
            "plant_name": self.plant_name,
            "plant_code": self.plant_code,
            "plant_address": self.plant_address,
            "plant_phone": self.plant_phone,
            "manager_name": self.manager_name,
            "capacity": self.capacity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "base_madre_plant_id": self.base_madre_plant_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            # Include company info for convenience
            "company_name": self.company.name if self.company else None,
        }
