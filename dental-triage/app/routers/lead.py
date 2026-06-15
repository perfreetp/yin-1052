from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead import LeadStatusEnum
from app.schemas.lead import LeadCreate, LeadOut, LeadMerge, DuplicateCheckResult
from app.services import lead_service

router = APIRouter(prefix="/leads", tags=["线索入口"])


@router.post("", response_model=LeadOut, summary="接收新咨询线索")
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead = lead_service.create_lead(db, data)
    return lead


@router.get("", response_model=List[LeadOut], summary="查询线索列表")
def list_leads(
    skip: int = 0,
    limit: int = 50,
    status: Optional[LeadStatusEnum] = None,
    db: Session = Depends(get_db),
):
    return lead_service.list_leads(db, skip, limit, status)


@router.get("/check-duplicate", response_model=DuplicateCheckResult, summary="重复咨询检查")
def check_duplicate(phone: str, db: Session = Depends(get_db)):
    return lead_service.check_duplicate(db, phone)


@router.get("/duplicates/{phone}", response_model=List[LeadOut], summary="查询同一电话的所有线索")
def get_duplicates(phone: str, db: Session = Depends(get_db)):
    return lead_service.get_duplicates_for_phone(db, phone)


@router.post("/merge", response_model=LeadOut, summary="合并重复线索")
def merge_leads(data: LeadMerge, db: Session = Depends(get_db)):
    try:
        return lead_service.merge_leads(db, data.source_lead_id, data.target_lead_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{lead_id}", response_model=LeadOut, summary="查询线索详情")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = lead_service.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")
    return lead
