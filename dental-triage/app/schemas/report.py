from typing import Optional, List
from pydantic import BaseModel, Field


class ClinicConversionReport(BaseModel):
    clinic_id: int
    clinic_name: str
    total_leads: int = 0
    triaged_count: int = 0
    dispatched_count: int = 0
    arrived_count: int = 0
    no_show_count: int = 0
    conversion_rate: float = 0.0
    no_show_rate: float = 0.0
    triage_hit_count: int = 0
    triage_partial_count: int = 0
    triage_miss_count: int = 0
    triage_total_confirmed: int = 0
    triage_accuracy_rate: float = 0.0
    triage_miss_rate: float = 0.0


class TriageHitReport(BaseModel):
    hit_count: int = 0
    partial_count: int = 0
    miss_count: int = 0
    total_confirmed: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0


class DirectionDistribution(BaseModel):
    direction: str
    count: int
    arrived_count: int = 0
    conversion_rate: float = 0.0


class NoShowReasonDistribution(BaseModel):
    reason: str
    count: int
    percentage: float = 0.0


class ChannelReport(BaseModel):
    channel: str
    total: int = 0
    arrived: int = 0
    conversion_rate: float = 0.0


class OverallReport(BaseModel):
    total_leads: int = 0
    total_arrived: int = 0
    overall_conversion_rate: float = 0.0
    triage_hit_report: Optional[TriageHitReport] = None
    clinic_reports: List[ClinicConversionReport] = []
    direction_distribution: List[DirectionDistribution] = []
    no_show_reasons: List[NoShowReasonDistribution] = []
    channel_reports: List[ChannelReport] = []
