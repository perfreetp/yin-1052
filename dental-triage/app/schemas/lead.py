from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.lead import ChannelEnum, LeadStatusEnum


class LeadCreate(BaseModel):
    patient_name: str = Field(..., max_length=50, description="患者姓名")
    patient_phone: str = Field(..., max_length=30, description="患者电话")
    channel: ChannelEnum = Field(..., description="咨询渠道")
    chief_complaint: str = Field(..., description="主诉内容")
    keywords: Optional[str] = Field(None, description="主诉关键词，逗号分隔")
    preferred_time: Optional[str] = Field(None, description="期望就诊时间")
    patient_latitude: Optional[float] = Field(None, description="患者位置纬度")
    patient_longitude: Optional[float] = Field(None, description="患者位置经度")


class LeadMerge(BaseModel):
    source_lead_id: int = Field(..., description="被合并的线索ID")
    target_lead_id: int = Field(..., description="保留的目标线索ID")


class LeadOut(BaseModel):
    id: int
    patient_name: str
    patient_phone: str
    channel: ChannelEnum
    chief_complaint: str
    keywords: Optional[str]
    preferred_time: Optional[str]
    patient_latitude: Optional[float]
    patient_longitude: Optional[float]
    status: LeadStatusEnum
    is_duplicate: bool
    merged_into_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool
    existing_lead_id: Optional[int] = None
    existing_lead_status: Optional[LeadStatusEnum] = None
