from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from loguru import logger

from server.dependencies import get_db_service
from server.services.db_service import DBService
from server.models.websockets import LogMessage # 로그 메시지 모델 임포트

router = APIRouter(
    prefix="/api/logs",
    tags=["Logs (HTTP)"]
)

@router.get(
    "/", 
    response_model=List[LogMessage],
    summary="Get Archived Event Logs",
    description="Retrieves a list of the most recent event logs from the database, sorted by timestamp."
)
def get_archived_logs(
    limit: int = Query(50, ge=1, le=200, description="The maximum number of logs to return."),
    db_service: DBService = Depends(get_db_service)
):
    """
    Fetches a list of past event logs stored in the database.
    This is typically used to populate the UI when it first loads.
    
    - **limit**: Specifies the number of recent logs to retrieve.
    """
    try:
        logger.info(f"Fetching last {limit} logs from the database.")
        events = db_service.get_events(limit=limit)
        # Pydantic 모델 리스트로 변환하여 응답 (데이터 검증)
        # get_events가 이미 딕셔너리 리스트를 반환하므로, FastAPI가 자동으로 검증/변환합니다.
        return events
    except Exception as e:
        logger.error(f"Error fetching logs from database: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while fetching logs."
        )