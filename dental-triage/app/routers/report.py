from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import OverallReport
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["运营复盘"])


@router.get("/overall", response_model=OverallReport, summary="综合运营报表")
def overall_report(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return report_service.generate_overall_report(db, start_date, end_date)
