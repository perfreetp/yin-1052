from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dispatch import DispatchStatusEnum
from app.schemas.dispatch import DispatchRequest, DispatchOut, ClinicRecommendation, DoctorRecommendation
from app.services import dispatch_service

router = APIRouter(prefix="/dispatch", tags=["派单中心"])


@router.post("", response_model=DispatchOut, summary="自动派单")
def auto_dispatch(req: DispatchRequest, db: Session = Depends(get_db)):
    try:
        return dispatch_service.auto_dispatch(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommend-clinics", response_model=List[ClinicRecommendation], summary="推荐院区")
def recommend_clinics(
    patient_lat: Optional[float] = None,
    patient_lon: Optional[float] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return dispatch_service.recommend_clinics(db, patient_lat, patient_lon, direction)


@router.get("/recommend-doctors", response_model=List[DoctorRecommendation], summary="推荐医生")
def recommend_doctors(
    clinic_id: Optional[int] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return dispatch_service.recommend_doctors(db, clinic_id, direction)


@router.patch("/{dispatch_id}/status", response_model=DispatchOut, summary="更新派单状态")
def update_status(dispatch_id: int, status: DispatchStatusEnum, db: Session = Depends(get_db)):
    try:
        return dispatch_service.update_dispatch_status(db, dispatch_id, status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{lead_id}", response_model=DispatchOut, summary="查询线索的派单")
def get_dispatch(lead_id: int, db: Session = Depends(get_db)):
    dispatch = dispatch_service.get_dispatch_by_lead(db, lead_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="派单记录不存在")
    return dispatch
