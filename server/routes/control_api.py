from fastapi import APIRouter, Depends, Request
from loguru import logger
from multiprocessing import Queue

from server.dependencies import get_command_queue

router = APIRouter()

@router.post("/start_automatic", summary="운전 모드 시작 요청")
def start_automatic_mode(request: Request, command_queue: Queue = Depends(get_command_queue)):
    """
    Vision Worker에 '운전 모드(AUTOMATIC)' 시작 명령을 전송합니다.
    안전 확인 및 최종 실행은 Worker가 담당합니다.
    """
    logger.info("API 요청: '운전 모드' 시작 명령을 Worker에 전송합니다.")
    command_queue.put({"command": "START_AUTOMATIC"})
    return {"message": "Automatic mode start command sent to worker."}

@router.post("/start_maintenance", summary="정비 모드 시작 요청 (LOTO)")
def start_maintenance_mode(request: Request, command_queue: Queue = Depends(get_command_queue)):
    """
    Vision Worker에 '정비 모드(MAINTENANCE)' 시작 명령을 전송합니다.
    """
    logger.info("API 요청: '정비 모드' 시작 명령을 Worker에 전송합니다.")
    command_queue.put({"command": "START_MAINTENANCE"})
    return {"message": "Maintenance mode start command sent to worker."}

@router.post("/stop", summary="시스템 전체 정지 요청")
def stop_system(request: Request, command_queue: Queue = Depends(get_command_queue)):
    """
    Vision Worker에 시스템 전체 정지 명령을 전송합니다.
    """
    logger.info("API 요청: 시스템 전체 정지 명령을 Worker에 전송합니다.")
    command_queue.put({"command": "STOP"})
    return {"message": "System stop command sent to worker."}

# 참고: 상태 조회(get_status) API는 app.py의 메인 /status 엔드포인트로 역할이 이전되었습니다.
# 해당 API는 Worker 프로세스의 생존 여부만 확인합니다.
# 상세한 시스템 상태(모드, 속도 등)는 Worker가 관리하며, 필요한 경우 WebSocket을 통해 UI로 전송됩니다.