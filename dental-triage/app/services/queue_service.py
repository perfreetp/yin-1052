from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStatusEnum
from app.models.triage import TriageRecord
from app.models.dispatch import Dispatch
from app.schemas.queue import (
    QueueLeadItem,
    QueueGroup,
    DispatchQueueResponse,
)


def _lead_to_queue_item(lead: Lead, triage: TriageRecord | None = None) -> QueueLeadItem:
    return QueueLeadItem(
        lead_id=lead.id,
        patient_name=lead.patient_name,
        patient_phone=lead.patient_phone,
        channel=lead.channel,
        chief_complaint=lead.chief_complaint,
        keywords=lead.keywords,
        preferred_time=lead.preferred_time,
        status=lead.status,
        direction=triage.direction if triage else None,
        is_urgent=triage.is_urgent if triage else False,
        urgency_reason=triage.urgency_reason if triage else None,
        created_at=lead.created_at,
    )


def get_dispatch_queue(db: Session) -> DispatchQueueResponse:
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=72)

    triaged_leads = (
        db.query(Lead)
        .filter(
            Lead.status == LeadStatusEnum.TRIAGED,
            Lead.is_duplicate == False,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.desc())
        .all()
    )
    triaged_lead_ids = [l.id for l in triaged_leads]
    triage_map = {}
    if triaged_lead_ids:
        triages = db.query(TriageRecord).filter(TriageRecord.lead_id.in_(triaged_lead_ids)).all()
        triage_map = {t.lead_id: t for t in triages}

    urgent_items = [
        _lead_to_queue_item(l, triage_map.get(l.id))
        for l in triaged_leads
        if triage_map.get(l.id) and triage_map[l.id].is_urgent
    ]

    dispatched_lead_ids = set()
    if triaged_lead_ids:
        disps = db.query(Dispatch).filter(Dispatch.lead_id.in_(triaged_lead_ids)).all()
        dispatched_lead_ids = set(d.lead_id for d in disps)

    pending_dispatch_items = [
        _lead_to_queue_item(l, triage_map.get(l.id))
        for l in triaged_leads
        if l.id not in dispatched_lead_ids
    ]

    dup_leads = (
        db.query(Lead)
        .filter(
            Lead.is_duplicate == True,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.desc())
        .all()
    )
    dup_triage_ids = [l.id for l in dup_leads]
    dup_triage_map = {}
    if dup_triage_ids:
        dup_triages = db.query(TriageRecord).filter(TriageRecord.lead_id.in_(dup_triage_ids)).all()
        dup_triage_map = {t.lead_id: t for t in dup_triages}
    duplicate_items = [
        _lead_to_queue_item(l, dup_triage_map.get(l.id))
        for l in dup_leads
    ]

    pending_leads = (
        db.query(Lead)
        .filter(
            Lead.status == LeadStatusEnum.PENDING,
            Lead.is_duplicate == False,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.desc())
        .all()
    )
    pending_items = [_lead_to_queue_item(l) for l in pending_leads]

    groups = [
        QueueGroup(
            name="急痛急肿（优先）",
            key="urgent",
            priority=1,
            count=len(urgent_items),
            leads=urgent_items,
        ),
        QueueGroup(
            name="待分诊",
            key="pending_triage",
            priority=2,
            count=len(pending_items),
            leads=pending_items,
        ),
        QueueGroup(
            name="已分诊待派单",
            key="pending_dispatch",
            priority=3,
            count=len(pending_dispatch_items),
            leads=pending_dispatch_items,
        ),
        QueueGroup(
            name="重复咨询未合并",
            key="duplicates",
            priority=4,
            count=len(duplicate_items),
            leads=duplicate_items,
        ),
    ]

    total = sum(g.count for g in groups)
    return DispatchQueueResponse(total_pending=total, groups=groups)
