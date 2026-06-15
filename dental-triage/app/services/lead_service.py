from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStatusEnum
from app.schemas.lead import LeadCreate, DuplicateCheckResult


def check_duplicate(db: Session, phone: str, hours: int = 72) -> DuplicateCheckResult:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    existing = (
        db.query(Lead)
        .filter(
            Lead.patient_phone == phone,
            Lead.created_at >= cutoff,
            Lead.is_duplicate == False,
            Lead.status != LeadStatusEnum.CANCELLED,
        )
        .order_by(Lead.created_at.desc())
        .first()
    )
    if existing:
        return DuplicateCheckResult(
            is_duplicate=True,
            existing_lead_id=existing.id,
            existing_lead_status=existing.status,
        )
    return DuplicateCheckResult(is_duplicate=False)


def create_lead(db: Session, data: LeadCreate) -> Lead:
    dup = check_duplicate(db, data.patient_phone)
    lead = Lead(
        patient_name=data.patient_name,
        patient_phone=data.patient_phone,
        channel=data.channel,
        chief_complaint=data.chief_complaint,
        keywords=data.keywords,
        preferred_time=data.preferred_time,
        patient_latitude=data.patient_latitude,
        patient_longitude=data.patient_longitude,
        is_duplicate=dup.is_duplicate,
        merged_into_id=dup.existing_lead_id if dup.is_duplicate else None,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def merge_leads(db: Session, source_id: int, target_id: int) -> Lead:
    source = db.query(Lead).filter(Lead.id == source_id).first()
    target = db.query(Lead).filter(Lead.id == target_id).first()
    if not source or not target:
        raise ValueError("线索不存在")
    source.is_duplicate = True
    source.merged_into_id = target_id
    source.status = LeadStatusEnum.CANCELLED
    if source.chief_complaint and source.chief_complaint not in (target.chief_complaint or ""):
        target.chief_complaint = f"{target.chief_complaint or ''}；合并自#{source_id}: {source.chief_complaint}"
    if source.keywords and source.keywords not in (target.keywords or ""):
        existing_kw = set((target.keywords or "").split(",")) if target.keywords else set()
        new_kw = set(source.keywords.split(","))
        target.keywords = ",".join(existing_kw | new_kw)
    db.commit()
    db.refresh(target)
    return target


def get_lead(db: Session, lead_id: int) -> Optional[Lead]:
    return db.query(Lead).filter(Lead.id == lead_id).first()


def list_leads(db: Session, skip: int = 0, limit: int = 50, status: Optional[LeadStatusEnum] = None):
    q = db.query(Lead).filter(Lead.is_duplicate == False)
    if status:
        q = q.filter(Lead.status == status)
    return q.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()


def get_duplicates_for_phone(db: Session, phone: str):
    return db.query(Lead).filter(Lead.patient_phone == phone).order_by(Lead.created_at.desc()).all()
