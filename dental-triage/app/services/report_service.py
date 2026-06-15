from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStatusEnum, ChannelEnum
from app.models.triage import TriageRecord
from app.models.dispatch import Dispatch
from app.models.arrival import ArrivalConfirmation, ArrivalStatusEnum, TriageHitEnum
from app.models.clinic import Clinic
from app.schemas.report import (
    ClinicConversionReport,
    TriageHitReport,
    DirectionDistribution,
    NoShowReasonDistribution,
    ChannelReport,
    OverallReport,
)


def _date_filter(query, model, start_date: Optional[str], end_date: Optional[str]):
    if start_date:
        query = query.filter(model.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(model.created_at <= datetime.fromisoformat(end_date))
    return query


def generate_overall_report(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> OverallReport:
    q = db.query(Lead).filter(Lead.is_duplicate == False)
    q = _date_filter(q, Lead, start_date, end_date)
    leads = q.all()

    total_leads = len(leads)
    total_arrived = len([l for l in leads if l.status == LeadStatusEnum.ARRIVED])
    overall_rate = round(total_arrived / total_leads * 100, 2) if total_leads > 0 else 0.0

    lead_ids = [l.id for l in leads]

    triage_hit = _build_triage_hit_report(db, lead_ids)
    clinic_reports = _build_clinic_reports(db, lead_ids)
    direction_dist = _build_direction_distribution(db, lead_ids)
    no_show_reasons = _build_no_show_reasons(db, lead_ids)
    channel_reports = _build_channel_reports(leads)

    return OverallReport(
        total_leads=total_leads,
        total_arrived=total_arrived,
        overall_conversion_rate=overall_rate,
        triage_hit_report=triage_hit,
        clinic_reports=clinic_reports,
        direction_distribution=direction_dist,
        no_show_reasons=no_show_reasons,
        channel_reports=channel_reports,
    )


def _build_triage_hit_report(db: Session, lead_ids: list[int]) -> TriageHitReport:
    if not lead_ids:
        return TriageHitReport()
    arrivals = db.query(ArrivalConfirmation).filter(
        ArrivalConfirmation.lead_id.in_(lead_ids),
        ArrivalConfirmation.arrival_status == ArrivalStatusEnum.ARRIVED,
        ArrivalConfirmation.triage_hit.isnot(None),
    ).all()
    hit = len([a for a in arrivals if a.triage_hit == TriageHitEnum.HIT])
    partial = len([a for a in arrivals if a.triage_hit == TriageHitEnum.PARTIAL])
    miss = len([a for a in arrivals if a.triage_hit == TriageHitEnum.MISS])
    total = hit + partial + miss
    return TriageHitReport(
        hit_count=hit,
        partial_count=partial,
        miss_count=miss,
        total_confirmed=total,
        hit_rate=round(hit / total * 100, 2) if total else 0.0,
        miss_rate=round(miss / total * 100, 2) if total else 0.0,
    )


def _build_clinic_reports(db: Session, lead_ids: list[int]) -> list[ClinicConversionReport]:
    if not lead_ids:
        return []
    clinics = db.query(Clinic).all()
    reports = []
    for c in clinics:
        dispatches = db.query(Dispatch).filter(
            Dispatch.clinic_id == c.id,
            Dispatch.lead_id.in_(lead_ids),
        ).all()
        disp_lead_ids = [d.lead_id for d in dispatches]
        if not disp_lead_ids:
            continue
        arrived = db.query(ArrivalConfirmation).filter(
            ArrivalConfirmation.lead_id.in_(disp_lead_ids),
            ArrivalConfirmation.arrival_status == ArrivalStatusEnum.ARRIVED,
        ).count()
        no_show = db.query(ArrivalConfirmation).filter(
            ArrivalConfirmation.lead_id.in_(disp_lead_ids),
            ArrivalConfirmation.arrival_status == ArrivalStatusEnum.NOT_ARRIVED,
        ).count()
        total_disp = len(disp_lead_ids)
        reports.append(ClinicConversionReport(
            clinic_id=c.id,
            clinic_name=c.name,
            total_leads=total_disp,
            triaged_count=0,
            dispatched_count=total_disp,
            arrived_count=arrived,
            no_show_count=no_show,
            conversion_rate=round(arrived / total_disp * 100, 2) if total_disp else 0.0,
            no_show_rate=round(no_show / total_disp * 100, 2) if total_disp else 0.0,
        ))
    return reports


def _build_direction_distribution(db: Session, lead_ids: list[int]) -> list[DirectionDistribution]:
    if not lead_ids:
        return []
    triages = db.query(TriageRecord).filter(TriageRecord.lead_id.in_(lead_ids)).all()
    counter = Counter(t.direction for t in triages)
    results = []
    for direction, count in counter.most_common():
        t_lead_ids = [t.lead_id for t in triages if t.direction == direction]
        arrived = db.query(ArrivalConfirmation).filter(
            ArrivalConfirmation.lead_id.in_(t_lead_ids),
            ArrivalConfirmation.arrival_status == ArrivalStatusEnum.ARRIVED,
        ).count()
        results.append(DirectionDistribution(
            direction=direction,
            count=count,
            arrived_count=arrived,
            conversion_rate=round(arrived / count * 100, 2) if count else 0.0,
        ))
    return results


def _build_no_show_reasons(db: Session, lead_ids: list[int]) -> list[NoShowReasonDistribution]:
    if not lead_ids:
        return []
    arrivals = db.query(ArrivalConfirmation).filter(
        ArrivalConfirmation.lead_id.in_(lead_ids),
        ArrivalConfirmation.arrival_status == ArrivalStatusEnum.NOT_ARRIVED,
        ArrivalConfirmation.no_show_reason.isnot(None),
    ).all()
    counter = Counter(a.no_show_reason for a in arrivals)
    total = sum(counter.values())
    results = []
    for reason, count in counter.most_common():
        results.append(NoShowReasonDistribution(
            reason=reason,
            count=count,
            percentage=round(count / total * 100, 2) if total else 0.0,
        ))
    return results


def _build_channel_reports(leads: list[Lead]) -> list[ChannelReport]:
    counter = Counter(l.channel for l in leads)
    arrived_by_channel = Counter(
        l.channel for l in leads if l.status == LeadStatusEnum.ARRIVED
    )
    results = []
    for channel, total in counter.most_common():
        arrived = arrived_by_channel.get(channel, 0)
        results.append(ChannelReport(
            channel=channel.value if isinstance(channel, ChannelEnum) else str(channel),
            total=total,
            arrived=arrived,
            conversion_rate=round(arrived / total * 100, 2) if total else 0.0,
        ))
    return results
