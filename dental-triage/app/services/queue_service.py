from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import (
    SLA_NORMAL_TRIAGE_HOURS,
    SLA_URGENT_TRIAGE_HOURS,
    SLA_NORMAL_DISPATCH_HOURS,
    SLA_URGENT_DISPATCH_HOURS,
)
from app.models.lead import Lead, LeadStatusEnum
from app.models.triage import TriageRecord
from app.models.dispatch import Dispatch
from app.models.arrival import ArrivalConfirmation, ArrivalStatusEnum, TriageHitEnum
from app.models.clinic import Clinic
from app.schemas.queue import (
    QueueLeadItem,
    QueueGroup,
    DispatchQueueResponse,
    ClinicTriageLeadItem,
    ClinicTriageDetailResponse,
)


def _build_queue_item(
    lead: Lead,
    triage: TriageRecord | None = None,
    stage: str = "pending",
) -> QueueLeadItem:
    now = datetime.utcnow()
    is_overdue = False
    overdue_hours: float | None = None
    overdue_reason: str | None = None

    if stage == "dispatch" and triage:
        sla_hours = SLA_URGENT_DISPATCH_HOURS if triage.is_urgent else SLA_NORMAL_DISPATCH_HOURS
        triage_time = triage.triaged_at or lead.created_at
        elapsed = (now - triage_time).total_seconds() / 3600
        if elapsed > sla_hours:
            is_overdue = True
            overdue_hours = round(elapsed - sla_hours, 1)
            tag = "急痛" if triage.is_urgent else "普通"
            overdue_reason = f"派单已超时{overdue_hours}小时（{tag}SLA{sla_hours}小时）"
    elif stage == "triage_pending":
        sla_hours = SLA_NORMAL_TRIAGE_HOURS
        elapsed = (now - lead.created_at).total_seconds() / 3600
        if elapsed > sla_hours:
            is_overdue = True
            overdue_hours = round(elapsed - sla_hours, 1)
            overdue_reason = f"待分诊已超时{overdue_hours}小时（SLA{sla_hours}小时）"
    elif stage == "urgent":
        sla_hours = SLA_URGENT_DISPATCH_HOURS
        triage_time = triage.triaged_at or lead.created_at if triage else lead.created_at
        elapsed = (now - triage_time).total_seconds() / 3600
        if elapsed > sla_hours:
            is_overdue = True
            overdue_hours = round(elapsed - sla_hours, 1)
            overdue_reason = f"急痛派单已超时{overdue_hours}小时（SLA{sla_hours}小时）"

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
        is_overdue=is_overdue,
        overdue_hours=overdue_hours,
        overdue_reason=overdue_reason,
    )


def _sort_items(items: list[QueueLeadItem]) -> list[QueueLeadItem]:
    return sorted(items, key=lambda x: (0 if x.is_overdue else 1, x.created_at))


def _build_group(
    name: str,
    key: str,
    priority: int,
    items: list[QueueLeadItem],
) -> QueueGroup:
    sorted_items = _sort_items(items)
    overdue_count = len([x for x in sorted_items if x.is_overdue])
    return QueueGroup(
        name=name,
        key=key,
        priority=priority,
        count=len(sorted_items),
        overdue_count=overdue_count,
        leads=sorted_items,
    )


def get_dispatch_queue(db: Session) -> DispatchQueueResponse:
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=72)

    pending_leads = (
        db.query(Lead)
        .filter(
            Lead.status == LeadStatusEnum.PENDING,
            Lead.is_duplicate == False,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.asc())
        .all()
    )

    triaged_leads = (
        db.query(Lead)
        .filter(
            Lead.status == LeadStatusEnum.TRIAGED,
            Lead.is_duplicate == False,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.asc())
        .all()
    )
    triaged_lead_ids = [l.id for l in triaged_leads]
    triage_map: dict[int, TriageRecord] = {}
    if triaged_lead_ids:
        triages = db.query(TriageRecord).filter(TriageRecord.lead_id.in_(triaged_lead_ids)).all()
        triage_map = {t.lead_id: t for t in triages}

    dispatched_lead_ids = set()
    if triaged_lead_ids:
        disps = db.query(Dispatch).filter(Dispatch.lead_id.in_(triaged_lead_ids)).all()
        dispatched_lead_ids = set(d.lead_id for d in disps)

    dup_leads = (
        db.query(Lead)
        .filter(
            Lead.is_duplicate == True,
            Lead.created_at >= cutoff,
        )
        .order_by(Lead.created_at.asc())
        .all()
    )
    dup_triage_ids = [l.id for l in dup_leads]
    dup_triage_map: dict[int, TriageRecord] = {}
    if dup_triage_ids:
        dup_triages = db.query(TriageRecord).filter(TriageRecord.lead_id.in_(dup_triage_ids)).all()
        dup_triage_map = {t.lead_id: t for t in dup_triages}

    urgent_items: list[QueueLeadItem] = []
    pending_dispatch_items: list[QueueLeadItem] = []
    for l in triaged_leads:
        if l.id in dispatched_lead_ids:
            continue
        triage = triage_map.get(l.id)
        if triage and triage.is_urgent:
            urgent_items.append(_build_queue_item(l, triage, stage="urgent"))
        else:
            pending_dispatch_items.append(_build_queue_item(l, triage, stage="dispatch"))

    pending_triage_items = [
        _build_queue_item(l, stage="triage_pending")
        for l in pending_leads
    ]

    duplicate_items = [
        _build_queue_item(l, dup_triage_map.get(l.id), stage="pending")
        for l in dup_leads
    ]

    all_items = urgent_items + pending_triage_items + pending_dispatch_items + duplicate_items
    total_overdue = len([x for x in all_items if x.is_overdue])

    overdue_seen: set[int] = set()
    overdue_items: list[QueueLeadItem] = []
    for item in all_items:
        if item.is_overdue and item.lead_id not in overdue_seen:
            overdue_seen.add(item.lead_id)
            overdue_items.append(item)

    groups = [
        _build_group("急痛急肿（优先）", "urgent", 1, urgent_items),
        _build_group("即将超时", "overdue", 2, overdue_items),
        _build_group("待分诊", "pending_triage", 3, pending_triage_items),
        _build_group("已分诊待派单", "pending_dispatch", 4, pending_dispatch_items),
        _build_group("重复咨询未合并", "duplicates", 5, duplicate_items),
    ]

    total = sum(g.count for g in groups)
    return DispatchQueueResponse(total_pending=total, total_overdue=total_overdue, groups=groups)


def get_clinic_triage_detail(
    db: Session,
    clinic_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ClinicTriageDetailResponse:
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise ValueError("院区不存在")

    q = db.query(Dispatch).filter(Dispatch.clinic_id == clinic_id)
    if start_date:
        q = q.filter(Dispatch.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(Dispatch.created_at <= datetime.fromisoformat(end_date))
    dispatches = q.all()
    disp_lead_ids = [d.lead_id for d in dispatches]

    if not disp_lead_ids:
        return ClinicTriageDetailResponse(clinic_id=clinic_id, clinic_name=clinic.name)

    lead_map = {l.id: l for l in db.query(Lead).filter(Lead.id.in_(disp_lead_ids)).all()}
    triage_map = {
        t.lead_id: t
        for t in db.query(TriageRecord).filter(TriageRecord.lead_id.in_(disp_lead_ids)).all()
    }
    arrival_map = {
        a.lead_id: a
        for a in db.query(ArrivalConfirmation).filter(
            ArrivalConfirmation.lead_id.in_(disp_lead_ids)
        ).all()
    }

    hit_leads: list[ClinicTriageLeadItem] = []
    partial_leads: list[ClinicTriageLeadItem] = []
    miss_leads: list[ClinicTriageLeadItem] = []
    no_show_leads: list[ClinicTriageLeadItem] = []

    for lid in disp_lead_ids:
        lead = lead_map.get(lid)
        if not lead:
            continue
        triage = triage_map.get(lid)
        arrival = arrival_map.get(lid)

        item = ClinicTriageLeadItem(
            lead_id=lead.id,
            patient_name=lead.patient_name,
            patient_phone=lead.patient_phone,
            channel=lead.channel,
            chief_complaint=lead.chief_complaint,
            triage_direction=triage.direction if triage else None,
            actual_direction=arrival.actual_direction if arrival else None,
            triage_hit=arrival.triage_hit if arrival else None,
            arrival_status=arrival.arrival_status.value if arrival else None,
            no_show_reason=arrival.no_show_reason if arrival else None,
            created_at=lead.created_at,
        )

        if arrival and arrival.arrival_status == ArrivalStatusEnum.NOT_ARRIVED:
            no_show_leads.append(item)
        elif arrival and arrival.triage_hit == TriageHitEnum.HIT:
            hit_leads.append(item)
        elif arrival and arrival.triage_hit == TriageHitEnum.PARTIAL:
            partial_leads.append(item)
        elif arrival and arrival.triage_hit == TriageHitEnum.MISS:
            miss_leads.append(item)

    return ClinicTriageDetailResponse(
        clinic_id=clinic_id,
        clinic_name=clinic.name,
        hit_leads=hit_leads,
        partial_leads=partial_leads,
        miss_leads=miss_leads,
        no_show_leads=no_show_leads,
    )
