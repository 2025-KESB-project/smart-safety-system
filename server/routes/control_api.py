from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from server.dependencies import get_state_manager, get_db_service, get_logic_facade
from server.state_manager import SystemStateManager
from server.models.status import SystemStatusResponse, ConfirmationResponse
from server.services.db_service import DBService
from logic.logic_facade import LogicFacade

router = APIRouter()

def get_complete_status(request: Request, state_manager: SystemStateManager, db_service: DBService) -> dict:
    """모든 서비스의 상태를 종합하여 완전한 상태 딕셔너리를 반환합니다."""
    status = state_manager.get_status()
    status['database_service'] = db_service.get_status()
    worker_task = request.app.state.worker_task
    status['background_worker_alive'] = not worker_task.done() if worker_task else False
    return status

@router.post(
    "/start_automatic",
    response_model=SystemStatusResponse,
    summary="운전 모드 시작",
    responses={
        202: {"model": ConfirmationResponse, "description": "2차 확인 필요"},
        409: {"description": "안전 문제로 인한 모드 전환 불가"}
    }
)
def start_automatic_mode(
    request: Request,
    state_manager: SystemStateManager = Depends(get_state_manager),
    db_service: DBService = Depends(get_db_service),
    logic_facade: LogicFacade = Depends(get_logic_facade),
    confirmed: bool = Query(False, description="사용자 2차 확인 여부")
):
    """
    안전 시스템의 논리적 상태를 '운전 모드(AUTOMATIC)'로 전환합니다.
    정비 모드(MAINTENANCE)에서 전환 시, 안전 조건을 확인하고 2차 확인을 요구할 수 있습니다.
    """
    current_mode = state_manager.get_mode()

    # 정비 모드에서 운전 모드로 전환하려는 경우, 안전 규칙을 적용합니다.
    if current_mode == 'MAINTENANCE':
        # 1. 실시간 위험 평가
        # 백그라운드 워커가 마지막으로 분석한 위험 평가 결과를 직접 사용합니다.
        last_analysis = logic_facade.last_risk_analysis or {"risk_factors": []}
        risk_factors = last_analysis.get("risk_factors", [])

        if risk_factors:
            logger.warning(f"LOTO 활성 중 위험({risk_factors})이 감지되어 운전 모드 전환을 차단했습니다.")
            raise HTTPException(
                status_code=409,
                detail=f"위험 구역 내 작업자 또는 센서({[f['type'] for f in risk_factors]})가 감지되어 운전 모드로 전환할 수 없습니다."
            )

        # 2. 사용자 2차 확인
        if not confirmed:
            logger.info("LOTO 해제 1단계: 2차 확인을 요구합니다.")
            return JSONResponse(
                status_code=202,
                content={
                    "confirmation_required": True,
                    "message": "작업자가 위험 구역에 없는지 다시 한번 확인했습니까?"
                }
            )

        logger.info("LOTO 해제 2단계: 사용자 확인 완료.")

    # 모든 검사를 통과했거나, 정비 모드가 아닌 상태에서 시작하는 경우
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
