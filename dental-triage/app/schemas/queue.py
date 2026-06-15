from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.lead import ChannelEnum, LeadStatusEnum
from app.models.arrival import TriageHitEnum


class QueueLeadItem(BaseModel):
    lead_id: int
    patient_name: str
    patient_phone: str
    channel: ChannelEnum
    chief_complaint: str
    keywords: Optional[str] = None
    preferred_time: Optional[str] = None
    status: LeadStatusEnum
    direction: Optional[str] = None
    is_urgent: bool = False
    urgency_reason: Optional[str] = None
    created_at: datetime
    is_overdue: bool = False
    overdue_hours: Optional[float] = None
    overdue_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class QueueGroup(BaseModel):
    name: str
    key: str
    priority: int
    count: int
    overdue_count: int = 0
    leads: List[QueueLeadItem] = []


class DispatchQueueResponse(BaseModel):
    total_pending: int
    total_overdue: int
    groups: List[QueueGroup]


class ClinicTriageLeadItem(BaseModel):
    lead_id: int
    patient_name: str
    patient_phone: str
    channel: ChannelEnum
    chief_complaint: str
    triage_direction: Optional[str] = None
    actual_direction: Optional[str] = None
    triage_hit: Optional[TriageHitEnum] = None
    arrival_status: Optional[str] = None
    no_show_reason: Optional[str] = None
    created_at: datetime


class ClinicTriageDetailResponse(BaseModel):
    clinic_id: int
    clinic_name: str
    hit_leads: List[ClinicTriageLeadItem] = []
    partial_leads: List[ClinicTriageLeadItem] = []
    miss_leads: List[ClinicTriageLeadItem] = []
    no_show_leads: List[ClinicTriageLeadItem] = []
