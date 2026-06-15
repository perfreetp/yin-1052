from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.triage import TriageRequest, TriageManualRequest, TriageOut, KeywordAnalysisResult
from app.services import triage_service

router = APIRouter(prefix="/triage", tags=["分诊规则"])


@router.post("/auto", response_model=TriageOut, summary="自动分诊")
def auto_triage(req: TriageRequest, db: Session = Depends(get_db)):
    try:
        return triage_service.auto_triage(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/manual", response_model=TriageOut, summary="人工分诊")
def manual_triage(req: TriageManualRequest, db: Session = Depends(get_db)):
    try:
        return triage_service.manual_triage(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analyze", response_model=KeywordAnalysisResult, summary="关键词分析（不保存）")
def analyze_keywords(chief_complaint: str, keywords: Optional[str] = None):
    return triage_service.analyze_keywords(chief_complaint, keywords)


@router.get("/{lead_id}", response_model=TriageOut, summary="查询线索的分诊记录")
def get_triage(lead_id: int, db: Session = Depends(get_db)):
    record = triage_service.get_triage_by_lead(db, lead_id)
    if not record:
        raise HTTPException(status_code=404, detail="分诊记录不存在")
    return record
