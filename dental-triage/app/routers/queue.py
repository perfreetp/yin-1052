from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.queue import DispatchQueueResponse
from app.services import queue_service

router = APIRouter(prefix="/queue", tags=["待处理队列"])


@router.get("", response_model=DispatchQueueResponse, summary="派单中心待处理队列")
def get_dispatch_queue(db: Session = Depends(get_db)):
    return queue_service.get_dispatch_queue(db)
