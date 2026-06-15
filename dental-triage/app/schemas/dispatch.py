from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.dispatch import DispatchStatusEnum


class DispatchRequest(BaseModel):
    lead_id: int = Field(..., description="线索ID")
    preferred_clinic_id: Optional[int] = Field(None, description="指定院区ID（可选）")
    preferred_doctor_id: Optional[int] = Field(None, description="指定医生ID（可选）")
    appointment_time: Optional[str] = Field(None, description="预约时间")
    dispatched_by: str = Field(..., description="派单操作人")


class DispatchOut(BaseModel):
    id: int
    lead_id: int
    clinic_id: int
    doctor_id: int
    appointment_time: Optional[str]
    status: DispatchStatusEnum
    dispatch_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClinicRecommendation(BaseModel):
    clinic_id: int
    clinic_name: str
    distance_km: Optional[float] = None
    is_open: bool = True
    business_hours: Optional[str] = None
    has_matching_doctor: bool
    available_doctors_count: int


class DoctorRecommendation(BaseModel):
    doctor_id: int
    doctor_name: str
    clinic_id: int
    clinic_name: str
    title: Optional[str]
    specialty_match: bool
    available_slots: int
