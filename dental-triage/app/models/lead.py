import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from app.database import Base


class ChannelEnum(str, enum.Enum):
    PHONE = "phone"
    ONLINE = "online"
    WALK_IN = "walk_in"
    REFERRAL = "referral"


class LeadStatusEnum(str, enum.Enum):
    PENDING = "pending"
    TRIAGED = "triaged"
    DISPATCHED = "dispatched"
    ARRIVED = "arrived"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (Index("ix_leads_phone_created", "patient_phone", "created_at"),)

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(50), nullable=False)
    patient_phone = Column(String(30), nullable=False, index=True)
    channel = Column(Enum(ChannelEnum), nullable=False, default=ChannelEnum.PHONE)
    chief_complaint = Column(Text, nullable=False)
    keywords = Column(String(255))
    preferred_time = Column(String(100))
    patient_latitude = Column(Float)
    patient_longitude = Column(Float)
    status = Column(Enum(LeadStatusEnum), nullable=False, default=LeadStatusEnum.PENDING)
    merged_into_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    merged_into = relationship("Lead", remote_side=[id], foreign_keys=[merged_into_id])
    triage_record = relationship("TriageRecord", back_populates="lead", uselist=False)
    dispatch = relationship("Dispatch", back_populates="lead", uselist=False)
    arrival = relationship("ArrivalConfirmation", back_populates="lead", uselist=False)
