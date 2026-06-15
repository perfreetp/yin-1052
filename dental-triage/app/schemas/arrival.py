from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.arrival import ArrivalStatusEnum, TriageHitEnum


class ArrivalConfirmRequest(BaseModel):
    lead_id: int = Field(..., description="线索ID")
    arrival_status: ArrivalStatusEnum = Field(..., description="到店状态")
    triage_hit: Optional[TriageHitEnum] = Field(None, description="分诊命中情况")
    triage_hit_note: Optional[str] = Field(None, description="命中说明")
    actual_direction: Optional[str] = Field(None, description="实际就诊方向")
    actual_doctor_id: Optional[int] = Field(None, description="实际就诊医生ID")
    no_show_reason: Optional[str] = Field(None, description="未到店原因")
    confirmed_by: str = Field(..., description="确认操作人")


class ArrivalOut(BaseModel):
    id: int
    lead_id: int
    arrival_status: ArrivalStatusEnum
    triage_hit: Optional[TriageHitEnum]
    triage_hit_note: Optional[str]
    actual_direction: Optional[str]
    actual_doctor_id: Optional[int]
    no_show_reason: Optional[str]
    confirmed_at: datetime
    confirmed_by: str

    model_config = {"from_attributes": True}
