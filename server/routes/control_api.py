from fastapi import APIRouter
from loguru import logger

from server.background_worker import start_conveyor, stop_conveyor, get_conveyor_status
from server.models.control import ControlResponse, ConveyorStatusResponse

router = APIRouter(
    prefix="/api/control",
    tags=["System Control"]
)

@router.post("/start", response_model=ControlResponse, summary="컨베이어 작동 시작")
def start_conveyor_endpoint():
    """
    컨베이어 벨트의 작동을 시작합니다. 
    이미 작동 중인 경우에도 상태를 그대로 유지합니다 (멱등성).
    """
    start_conveyor()
    message = "Request to start conveyor processed. Current status: ON"
    logger.info(message)
    return {"status": "success", "message": message}

@router.post("/stop", response_model=ControlResponse, summary="컨베이어 작동 정지")
def stop_conveyor_endpoint():
    """
    컨베이어 벨트의 작동을 정지합니다.
    이미 정지된 경우에도 상태를 그대로 유지합니다 (멱등성).
    """
    stop_conveyor()
    message = "Request to stop conveyor processed. Current status: OFF"
    logger.info(message)
    return {"status": "success", "message": message}

@router.get("/status", response_model=ConveyorStatusResponse, summary="컨베이어 현재 상태 조회")
def get_status_endpoint():
    """
    현재 컨베이어 벨트의 작동 상태(ON/OFF)를 조회합니다.
    """
    is_operating = get_conveyor_status()
    return {"is_operating": is_operating}