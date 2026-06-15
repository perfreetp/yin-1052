from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.queue import DispatchQueueResponse, ClinicTriageDetailResponse
from app.services import queue_service

router = APIRouter(prefix="/queue", tags=["待处理队列"])


@router.get("", response_model=DispatchQueueResponse, summary="调度看板：多桶视图")
def get_dispatch_queue(db: Session = Depends(get_db)):
    return queue_service.get_dispatch_queue(db)


@router.get("/clinic/{clinic_id}", response_model=ClinicTriageDetailResponse, summary="院区误派追踪明细")
def get_clinic_triage_detail(
    clinic_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        return queue_service.get_clinic_triage_detail(db, clinic_id, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
