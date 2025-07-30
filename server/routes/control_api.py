from fastapi import APIRouter, Depends
from loguru import logger

# 의존성 주입을 통해 중앙 관리 객체를 가져옵니다.
from server.dependencies import get_state_manager
from server.state_manager import SystemStateManager
from server.models.status import SystemStatusResponse

router = APIRouter()

@router.post("/start_automatic", response_model=SystemStatusResponse, summary="운전 모드 시작")
def start_automatic_mode(state_manager: SystemStateManager = Depends(get_state_manager)):
    """
    안전 시스템의 논리적 상태를 '운전 모드(AUTOMATIC)'로 전환합니다.
    실제 컨베이어의 제어는 백그라운드 워커와 로직 레이어가 담당합니다.
    """
    logger.info("API 요청: '운전 모드' 시작")
    status = state_manager.start_automatic_mode()
    # API 계층에서는 물리적 상태를 확신할 수 없으므로, 논리적 상태만 반환하거나 물리적 상태를 None으로 표시합니다.
    return SystemStatusResponse(**status, conveyor_is_on=None)

@router.post("/start_maintenance", response_model=SystemStatusResponse, summary="정비 모드 시작 (LOTO)")
def start_maintenance_mode(state_manager: SystemStateManager = Depends(get_state_manager)):
    """
    안전 시스템의 논리적 상태를 '정비 모드(MAINTENANCE)'로 전환합니다. (LOTO)
    이 API는 상태만 변경하며, 전원 차단은 백그라운드 로직에 의해 수행됩니다.
    """
    logger.info("API 요청: '정비 모드' 시작 (LOTO)")
    status = state_manager.start_maintenance_mode()
    return SystemStatusResponse(**status, conveyor_is_on=None)

@router.post("/stop", response_model=SystemStatusResponse, summary="시스템 전체 정지")
def stop_system(state_manager: SystemStateManager = Depends(get_state_manager)):
    """
    모든 시스템 작동을 중지하고 논리적 상태를 비활성으로 전환합니다.
    """
    logger.info("API 요청: 시스템 전체 정지")
    status = state_manager.stop_system_globally()
    # 시스템 정지 시에는 물리적으로도 확실히 꺼지므로 False로 반환할 수 있습니다.
    return SystemStatusResponse(**status, conveyor_is_on=False)

@router.get("/status", response_model=SystemStatusResponse, summary="시스템 현재 논리적 상태 조회")
def get_status(state_manager: SystemStateManager = Depends(get_state_manager)):
    """
    시스템의 현재 논리적 상태(모드)를 반환합니다.
    물리적 상태(conveyor_is_on)를 포함한 전체 상태는 /status 엔드포인트를 확인하세요.
    """
    status = state_manager.get_status()
    return SystemStatusResponse(**status, conveyor_is_on=None)