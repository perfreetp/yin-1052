import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ConsultationTypeEnum(str, enum.Enum):
    CLEANING = "cleaning"
    TREATMENT = "treatment"


class TriageRecord(Base):
    __tablename__ = "triage_records"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, unique=True, index=True)
    consultation_type = Column(Enum(ConsultationTypeEnum), nullable=False)
    direction = Column(String(50), nullable=False)
    is_urgent = Column(Boolean, default=False)
    urgency_reason = Column(String(255))
    recommended_clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True)
    script_hint = Column(Text)
    triaged_at = Column(DateTime, default=datetime.utcnow)
    triaged_by = Column(String(50))

    lead = relationship("Lead", back_populates="triage_record")
