from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(30))
    business_hours = Column(String(255))
    is_active = Column(Boolean, default=True)

    doctors = relationship("Doctor", back_populates="clinic")
    dispatches = relationship("Dispatch", back_populates="clinic")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    title = Column(String(50))
    specialties = Column(String(255))
    available_slots = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    clinic = relationship("Clinic", back_populates="doctors")
    dispatches = relationship("Dispatch", back_populates="doctor")
