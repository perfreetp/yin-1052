from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.triage import ConsultationTypeEnum


class TriageRequest(BaseModel):
    lead_id: int = Field(..., description="线索ID")
    triaged_by: str = Field(..., description="分诊操作人")


class TriageManualRequest(BaseModel):
    lead_id: int = Field(..., description="线索ID")
    consultation_type: ConsultationTypeEnum = Field(..., description="咨询类型")
    direction: str = Field(..., description="需求方向")
    is_urgent: bool = Field(False, description="是否急痛")
    urgency_reason: Optional[str] = Field(None, description="急痛原因")
    triaged_by: str = Field(..., description="分诊操作人")


class TriageOut(BaseModel):
    id: int
    lead_id: int
    consultation_type: ConsultationTypeEnum
    direction: str
    is_urgent: bool
    urgency_reason: Optional[str]
    recommended_clinic_id: Optional[int]
    script_hint: Optional[str]
    triaged_at: datetime
    triaged_by: str

    model_config = {"from_attributes": True}


class KeywordAnalysisResult(BaseModel):
    consultation_type: ConsultationTypeEnum
    direction: str
    is_urgent: bool
    urgency_reason: Optional[str] = None
    matched_keywords: List[str] = []
    script_hint: Optional[str] = None
