import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import CLINIC_SEARCH_RADIUS_KM
from app.models.lead import Lead, LeadStatusEnum
from app.models.triage import TriageRecord
from app.models.clinic import Clinic, Doctor
from app.models.dispatch import Dispatch, DispatchStatusEnum
from app.utils.time_utils import infer_target_weekday, is_clinic_open_on
from app.schemas.dispatch import (
    DispatchRequest,
    DispatchOut,
    ClinicRecommendation,
    DoctorRecommendation,
)


def _get_specialty_list(doctor):
    if not doctor.specialties:
        return []
    return [s.strip() for s in doctor.specialties.split(",")]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def recommend_clinics(
    db: Session,
    patient_lat: Optional[float],
    patient_lon: Optional[float],
    direction: Optional[str] = None,
    preferred_time: Optional[str] = None,
) -> List[ClinicRecommendation]:
    target_weekday = infer_target_weekday(preferred_time)
    clinics = db.query(Clinic).filter(Clinic.is_active == True).all()
    results = []
    for c in clinics:
        is_open = is_clinic_open_on(c.business_hours or "", target_weekday)
        if target_weekday is not None and not is_open:
            continue
        dist = None
        if patient_lat is not None and patient_lon is not None:
            dist = _haversine_km(patient_lat, patient_lon, c.latitude, c.longitude)
            if dist > CLINIC_SEARCH_RADIUS_KM:
                continue
        doctors = db.query(Doctor).filter(Doctor.clinic_id == c.id, Doctor.is_active == True).all()
        matching = doctors
        if direction:
            matching = [d for d in doctors if direction in _get_specialty_list(d)]
        results.append(
            ClinicRecommendation(
                clinic_id=c.id,
                clinic_name=c.name,
                distance_km=round(dist, 2) if dist is not None else None,
                is_open=is_open,
                business_hours=c.business_hours,
                has_matching_doctor=len(matching) > 0,
                available_doctors_count=len([d for d in matching if d.available_slots > 0]),
            )
        )
    results.sort(key=lambda x: x.distance_km if x.distance_km is not None else 9999)
    results.sort(key=lambda x: (0 if x.has_matching_doctor else 1))
    results.sort(key=lambda x: 0 if x.is_open else 1)
    return results


def recommend_doctors(
    db: Session,
    clinic_id: Optional[int] = None,
    direction: Optional[str] = None,
) -> List[DoctorRecommendation]:
    q = db.query(Doctor).filter(Doctor.is_active == True)
    if clinic_id:
        q = q.filter(Doctor.clinic_id == clinic_id)
    doctors = q.all()
    results = []
    for d in doctors:
        specialty_match = direction in _get_specialty_list(d) if direction else True
        clinic = db.query(Clinic).filter(Clinic.id == d.clinic_id).first()
        results.append(
            DoctorRecommendation(
                doctor_id=d.id,
                doctor_name=d.name,
                clinic_id=d.clinic_id,
                clinic_name=clinic.name if clinic else "",
                title=d.title,
                specialty_match=specialty_match,
                available_slots=d.available_slots,
            )
        )
    results.sort(key=lambda x: (0 if x.specialty_match else 1, -x.available_slots))
    return results


def _find_best_doctor(db: Session, clinic_id: int, direction: Optional[str]) -> Optional[Doctor]:
    doctors = (
        db.query(Doctor)
        .filter(Doctor.clinic_id == clinic_id, Doctor.is_active == True, Doctor.available_slots > 0)
        .all()
    )
    if direction:
        matched = [d for d in doctors if direction in _get_specialty_list(d)]
        if matched:
            return matched[0]
    if doctors:
        return doctors[0]
    return None


def auto_dispatch(db: Session, req: DispatchRequest) -> Dispatch:
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise ValueError("线索不存在")
    if lead.status != LeadStatusEnum.TRIAGED:
        raise ValueError(f"线索状态为 {lead.status.value}，需先完成分诊")

    triage = db.query(TriageRecord).filter(TriageRecord.lead_id == lead.id).first()
    if not triage:
        raise ValueError("未找到分诊记录")

    target_clinic_id = req.preferred_clinic_id or triage.recommended_clinic_id
    if not target_clinic_id:
        clinics = recommend_clinics(
            db, lead.patient_latitude, lead.patient_longitude,
            triage.direction, lead.preferred_time,
        )
        if clinics:
            best = [c for c in clinics if c.is_open and c.has_matching_doctor and c.available_doctors_count > 0]
            if not best:
                best = [c for c in clinics if c.has_matching_doctor and c.available_doctors_count > 0]
            target_clinic_id = (best[0] if best else clinics[0]).clinic_id if clinics else None

    if not target_clinic_id:
        raise ValueError("未找到合适的院区")

    doctor = None
    if req.preferred_doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == req.preferred_doctor_id, Doctor.is_active == True).first()
    if not doctor:
        doctor = _find_best_doctor(db, target_clinic_id, triage.direction)
    if not doctor:
        all_docs = db.query(Doctor).filter(Doctor.clinic_id == target_clinic_id, Doctor.is_active == True).first()
        doctor = all_docs
    if not doctor:
        raise ValueError("未找到合适的医生")

    reason_parts = []
    if triage.is_urgent:
        reason_parts.append("急痛优先")
    if triage.direction in _get_specialty_list(doctor):
        reason_parts.append(f"擅长匹配({triage.direction})")
    else:
        reason_parts.append(f"方向{triage.direction}，分配至{doctor.name}")
    if triage.recommended_clinic_id == target_clinic_id:
        reason_parts.append("距离推荐")

    dispatch = Dispatch(
        lead_id=lead.id,
        clinic_id=target_clinic_id,
        doctor_id=doctor.id,
        appointment_time=req.appointment_time,
        status=DispatchStatusEnum.ASSIGNED,
        dispatch_reason="；".join(reason_parts),
    )
    db.add(dispatch)
    doctor.available_slots = max(0, doctor.available_slots - 1)
    lead.status = LeadStatusEnum.DISPATCHED
    db.commit()
    db.refresh(dispatch)
    return dispatch


def update_dispatch_status(db: Session, dispatch_id: int, status: DispatchStatusEnum) -> Dispatch:
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise ValueError("派单不存在")
    dispatch.status = status
    if status == DispatchStatusEnum.CANCELLED:
        doctor = db.query(Doctor).filter(Doctor.id == dispatch.doctor_id).first()
        if doctor:
            doctor.available_slots += 1
        lead = db.query(Lead).filter(Lead.id == dispatch.lead_id).first()
        if lead:
            lead.status = LeadStatusEnum.CANCELLED
    db.commit()
    db.refresh(dispatch)
    return dispatch


def get_dispatch_by_lead(db: Session, lead_id: int) -> Optional[Dispatch]:
    return db.query(Dispatch).filter(Dispatch.lead_id == lead_id).first()
