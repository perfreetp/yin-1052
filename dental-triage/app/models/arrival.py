import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ArrivalStatusEnum(str, enum.Enum):
    ARRIVED = "arrived"
    NOT_ARRIVED = "not_arrived"


class TriageHitEnum(str, enum.Enum):
    HIT = "hit"
    PARTIAL = "partial"
    MISS = "miss"


class ArrivalConfirmation(Base):
    __tablename__ = "arrival_confirmations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, unique=True, index=True)
    arrival_status = Column(Enum(ArrivalStatusEnum), nullable=False)
    triage_hit = Column(Enum(TriageHitEnum), nullable=True)
    triage_hit_note = Column(Text)
    actual_direction = Column(String(50))
    actual_doctor_id = Column(Integer, nullable=True)
    no_show_reason = Column(String(100))
    confirmed_at = Column(DateTime, default=datetime.utcnow)
    confirmed_by = Column(String(50))

    lead = relationship("Lead", back_populates="arrival")
