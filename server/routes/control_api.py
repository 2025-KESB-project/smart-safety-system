from fastapi import APIRouter, Depends, Request
from loguru import logger

from server.dependencies import get_state_manager, get_db_service
from server.state_manager import SystemStateManager
from server.models.status import SystemStatusResponse
from server.services.db_service import DBService

router = APIRouter()

def get_complete_status(request: Request, state_manager: SystemStateManager, db_service: DBService) -> dict:
    """모든 서비스의 상태를 종합하여 완전한 상태 딕셔너리를 반환합니다."""
    # 1. StateManager로부터 논리적/물리적 상태를 모두 가져옵니다.
    status = state_manager.get_status()
    
    # 2. 다른 서비스들의 상태를 추가합니다.
    status['database_service'] = db_service.get_status()
    worker_task = request.app.state.worker_thread
    status['background_worker_alive'] = worker_task.is_alive() if worker_task else False
    
    return status

@router.post("/start_automatic", response_model=SystemStatusResponse, summary="운전 모드 시작")
def start_automatic_mode(
    request: Request,
    state_manager: SystemStateManager = Depends(get_state_manager),
    db_service: DBService = Depends(get_db_service)
):
    """
    안전 시스템의 논리적 상태를 '운전 모드(AUTOMATIC)'로 전환합니다.
    """
    logger.info("API 요청: '운전 모드' 시작")
    state_manager.start_automatic_mode()
    complete_status = get_complete_status(request, state_manager, db_service)
    return SystemStatusResponse(**complete_status)

@router.post("/start_maintenance", response_model=SystemStatusResponse, summary="정비 모드 시작 (LOTO)")
def start_maintenance_mode(
    request: Request,
    state_manager: SystemStateManager = Depends(get_state_manager),
    db_service: DBService = Depends(get_db_service)
):
    """
    안전 시스템의 논리적 상태를 '정비 모드(MAINTENANCE)'로 전환합니다.
    """
    logger.info("API 요청: '정비 모드' 시작 (LOTO)")
    state_manager.start_maintenance_mode()
    complete_status = get_complete_status(request, state_manager, db_service)
    return SystemStatusResponse(**complete_status)

@router.post("/stop", response_model=SystemStatusResponse, summary="시스템 전체 정지")
def stop_system(
    request: Request,
    state_manager: SystemStateManager = Depends(get_state_manager),
    db_service: DBService = Depends(get_db_service)
):
    """
    모든 시스템 작동을 중지하고 논리적 상태를 비활성으로 전환합니다.
    """
    logger.info("API 요청: 시스템 전체 정지")
    state_manager.stop_system_globally()
    complete_status = get_complete_status(request, state_manager, db_service)
    return SystemStatusResponse(**complete_status)

@router.get("/status", response_model=SystemStatusResponse, summary="시스템 현재 상태 조회")
def get_status(
    request: Request,
    state_manager: SystemStateManager = Depends(get_state_manager),
    db_service: DBService = Depends(get_db_service)
):
    """
    시스템의 모든 논리적, 물리적, 서비스 상태를 종합하여 반환합니다.
    """
    complete_status = get_complete_status(request, state_manager, db_service)
    return SystemStatusResponse(**complete_status)
