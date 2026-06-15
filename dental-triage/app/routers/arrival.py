from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.arrival import ArrivalConfirmRequest, ArrivalOut
from app.services import arrival_service

router = APIRouter(prefix="/arrival", tags=["到店确认"])


@router.post("", response_model=ArrivalOut, summary="到店确认")
def confirm_arrival(req: ArrivalConfirmRequest, db: Session = Depends(get_db)):
    try:
        return arrival_service.confirm_arrival(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lead_id}", response_model=ArrivalOut, summary="查询线索的到店确认")
def get_arrival(lead_id: int, db: Session = Depends(get_db)):
    record = arrival_service.get_arrival_by_lead(db, lead_id)
    if not record:
        raise HTTPException(status_code=404, detail="到店确认记录不存在")
    return record


@router.get("/no-show-reasons/list", response_model=list[str], summary="未到店原因列表")
def get_no_show_reasons():
    return arrival_service.get_no_show_reasons()
