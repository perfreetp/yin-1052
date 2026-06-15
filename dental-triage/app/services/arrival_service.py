from typing import Optional

from sqlalchemy.orm import Session

from app.config import NO_SHOW_REASONS
from app.models.lead import Lead, LeadStatusEnum
from app.models.triage import TriageRecord
from app.models.dispatch import Dispatch
from app.models.arrival import ArrivalConfirmation, ArrivalStatusEnum, TriageHitEnum
from app.schemas.arrival import ArrivalConfirmRequest


def confirm_arrival(db: Session, req: ArrivalConfirmRequest) -> ArrivalConfirmation:
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise ValueError("线索不存在")
    if lead.status not in (LeadStatusEnum.DISPATCHED, LeadStatusEnum.TRIAGED):
        raise ValueError(f"线索状态为 {lead.status.value}，无法确认到店")

    if req.arrival_status == ArrivalStatusEnum.NOT_ARRIVED:
        if not req.no_show_reason:
            raise ValueError("未到店需填写原因")
        lead.status = LeadStatusEnum.NO_SHOW
        triage_hit = None
    else:
        lead.status = LeadStatusEnum.ARRIVED
        triage = db.query(TriageRecord).filter(TriageRecord.lead_id == lead.id).first()
        if triage and req.actual_direction:
            if req.actual_direction == triage.direction:
                triage_hit = TriageHitEnum.HIT
            elif req.actual_direction in triage.direction or triage.direction in req.actual_direction:
                triage_hit = TriageHitEnum.PARTIAL
            else:
                triage_hit = TriageHitEnum.MISS
        else:
            triage_hit = req.triage_hit

    confirmation = ArrivalConfirmation(
        lead_id=lead.id,
        arrival_status=req.arrival_status,
        triage_hit=triage_hit,
        triage_hit_note=req.triage_hit_note,
        actual_direction=req.actual_direction,
        actual_doctor_id=req.actual_doctor_id,
        no_show_reason=req.no_show_reason,
        confirmed_by=req.confirmed_by,
    )
    db.add(confirmation)
    db.commit()
    db.refresh(confirmation)
    return confirmation


def get_arrival_by_lead(db: Session, lead_id: int) -> Optional[ArrivalConfirmation]:
    return db.query(ArrivalConfirmation).filter(ArrivalConfirmation.lead_id == lead_id).first()


def get_no_show_reasons() -> list[str]:
    return NO_SHOW_REASONS
