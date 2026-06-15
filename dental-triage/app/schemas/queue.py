from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.lead import ChannelEnum, LeadStatusEnum


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

    model_config = {"from_attributes": True}


class QueueGroup(BaseModel):
    name: str
    key: str
    priority: int
    count: int
    leads: List[QueueLeadItem] = []


class DispatchQueueResponse(BaseModel):
    total_pending: int
    groups: List[QueueGroup]
