import math
from typing import Optional

from sqlalchemy.orm import Session

from app.config import DIRECTION_KEYWORDS, URGENT_KEYWORDS, SCRIPT_TEMPLATES, CLINIC_SEARCH_RADIUS_KM
from app.models.lead import Lead, LeadStatusEnum
from app.models.triage import TriageRecord, ConsultationTypeEnum
from app.models.clinic import Clinic
from app.schemas.triage import TriageRequest, TriageManualRequest, KeywordAnalysisResult


def analyze_keywords(chief_complaint: str, keywords: Optional[str] = None) -> KeywordAnalysisResult:
    text = chief_complaint or ""
    if keywords:
        text = f"{text} {keywords}"
    text_lower = text.lower()

    is_urgent = False
    urgency_reason = None
    for kw in URGENT_KEYWORDS:
        if kw in text_lower:
            is_urgent = True
            urgency_reason = kw
            break

    matched_direction = "牙体牙髓"
    matched_keywords = []
    for direction, kws in DIRECTION_KEYWORDS.items():
        for kw in kws:
            if kw in text_lower:
                matched_direction = direction
                matched_keywords.append(kw)
                break
        if matched_keywords:
            break

    consultation_type = ConsultationTypeEnum.CLEANING
    cleaning_kws = DIRECTION_KEYWORDS.get("洁牙", [])
    if matched_direction != "洁牙":
        consultation_type = ConsultationTypeEnum.TREATMENT
    else:
        for kw in cleaning_kws:
            if kw in text_lower:
                consultation_type = ConsultationTypeEnum.CLEANING
                break

    script_hint = SCRIPT_TEMPLATES.get(matched_direction) or SCRIPT_TEMPLATES.get("牙体牙髓")
    if is_urgent:
        script_hint = SCRIPT_TEMPLATES.get("急痛", script_hint)

    return KeywordAnalysisResult(
        consultation_type=consultation_type,
        direction=matched_direction,
        is_urgent=is_urgent,
        urgency_reason=urgency_reason,
        matched_keywords=matched_keywords,
        script_hint=script_hint,
    )


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def recommend_clinic(db: Session, patient_lat: Optional[float], patient_lon: Optional[float]) -> Optional[int]:
    clinics = db.query(Clinic).filter(Clinic.is_active == True).all()
    if not clinics:
        return None
    if patient_lat is None or patient_lon is None:
        return clinics[0].id
    best_clinic = None
    best_dist = float("inf")
    for c in clinics:
        dist = _haversine_km(patient_lat, patient_lon, c.latitude, c.longitude)
        if dist < best_dist and dist <= CLINIC_SEARCH_RADIUS_KM:
            best_dist = dist
            best_clinic = c
    return best_clinic.id if best_clinic else clinics[0].id


def auto_triage(db: Session, req: TriageRequest) -> TriageRecord:
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise ValueError("线索不存在")
    if lead.status != LeadStatusEnum.PENDING:
        raise ValueError(f"线索状态为 {lead.status.value}，无法分诊")

    analysis = analyze_keywords(lead.chief_complaint, lead.keywords)
    clinic_id = recommend_clinic(db, lead.patient_latitude, lead.patient_longitude)

    record = TriageRecord(
        lead_id=lead.id,
        consultation_type=analysis.consultation_type,
        direction=analysis.direction,
        is_urgent=analysis.is_urgent,
        urgency_reason=analysis.urgency_reason,
        recommended_clinic_id=clinic_id,
        script_hint=analysis.script_hint,
        triaged_by=req.triaged_by,
    )
    db.add(record)
    lead.status = LeadStatusEnum.TRIAGED
    db.commit()
    db.refresh(record)
    return record


def manual_triage(db: Session, req: TriageManualRequest) -> TriageRecord:
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise ValueError("线索不存在")
    if lead.status != LeadStatusEnum.PENDING:
        raise ValueError(f"线索状态为 {lead.status.value}，无法分诊")

    script_hint = SCRIPT_TEMPLATES.get(req.direction)
    if req.is_urgent:
        script_hint = SCRIPT_TEMPLATES.get("急痛", script_hint)

    clinic_id = recommend_clinic(db, lead.patient_latitude, lead.patient_longitude)

    record = TriageRecord(
        lead_id=lead.id,
        consultation_type=req.consultation_type,
        direction=req.direction,
        is_urgent=req.is_urgent,
        urgency_reason=req.urgency_reason,
        recommended_clinic_id=clinic_id,
        script_hint=script_hint,
        triaged_by=req.triaged_by,
    )
    db.add(record)
    lead.status = LeadStatusEnum.TRIAGED
    db.commit()
    db.refresh(record)
    return record


def get_triage_by_lead(db: Session, lead_id: int) -> Optional[TriageRecord]:
    return db.query(TriageRecord).filter(TriageRecord.lead_id == lead_id).first()
