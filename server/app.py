import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from multiprocessing import Process, Queue

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# --------------------------------------------------------------------------
# 시스템 경로 및 로깅 설정
# --------------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent.parent.absolute()))
logger.remove()
logger.add(
    sys.stderr, level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
)

# --- 아키텍처 변경에 따른 임포트 수정 ---
from server.services.db_service import DBService
from server.services.zone_service import ZoneService
from server.services.websocket_service import WebSocketService
from vision_worker import run_worker_process # 분리된 워커 프로세스 진입점

# --- 라우터 임포트 ---
from server.routes import log_api, streaming, alert_ws, zone_api, control_api, log_ws

# --------------------------------------------------------------------------
# Queue 리스너 (워커 -> 서버)
# --------------------------------------------------------------------------
async def queue_listener(log_queue: Queue, app: FastAPI):
    """워커 프로세스로부터 오는 로그 및 알림을 처리합니다."""
    logger.info("Queue 리스너를 시작합니다.")
    db_service = app.state.db_service
    websocket_service = app.state.websocket_service
    loop = app.state.loop

    while True:
        if not log_queue.empty():
            message = log_queue.get()
            msg_type = message.get("type")
            data = message.get("data")
            
            if msg_type == "LOG":
                await db_service.log_event(data)
            elif msg_type == "ALERT":
                # WebSocket을 통해 UI로 긴급 알림 전송
                asyncio.run_coroutine_threadsafe(
                    websocket_service.broadcast_to_channel('alerts', data),
                    loop
                )
        await asyncio.sleep(0.1)

# --------------------------------------------------------------------------
# FastAPI Lifespan (서버 시작/종료 이벤트)
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 서버 시작 ---
    logger.info("FastAPI 서버 시작 프로세스를 개시합니다...")
    app.state.loop = asyncio.get_running_loop()

    # 1. 프로세스간 통신을 위한 Queue 생성
    command_queue = Queue()
    log_queue = Queue()
    frame_queue = Queue(maxsize=2)
    app.state.command_queue = command_queue
    app.state.frame_queue = frame_queue
    logger.info("프로세스 통신용 Queues 생성 완료.")

    # 2. 핵심 서비스 초기화 (DB, WebSocket 등)
    app.state.websocket_service = WebSocketService()
    app.state.db_service = DBService(loop=app.state.loop, websocket_service=app.state.websocket_service)
    app.state.zone_service = ZoneService()
    logger.success("핵심 서비스(DB, WS, Zone) 초기화 완료.")

    # 3. Vision Worker 프로세스 시작
    worker_process = Process(
        target=run_worker_process,
        args=(command_queue, log_queue, frame_queue),
        daemon=True
    )
    app.state.worker_process = worker_process
    worker_process.start()
    logger.success(f"Vision Worker 프로세스를 시작했습니다 (PID: {worker_process.pid}).")

    # 4. Queue 리스너를 비동기 태스크로 시작
    listener_task = asyncio.create_task(queue_listener(log_queue, app))
    app.state.listener_task = listener_task
    logger.success("Queue 리스너 태스크를 시작했습니다.")

    yield
    
    # --- 서버 종료 ---
    logger.info("FastAPI 서버가 종료됩니다...")
    if app.state.worker_process and app.state.worker_process.is_alive():
        logger.info("Vision Worker 프로세스에 종료 명령을 전송합니다.")
        app.state.command_queue.put({"command": "STOP"})
        app.state.worker_process.join(timeout=5) # 5초간 기다림
        if app.state.worker_process.is_alive():
            logger.warning("Vision Worker 프로세스가 정상적으로 종료되지 않아 강제 종료합니다.")
            app.state.worker_process.terminate()
    
    if app.state.listener_task and not app.state.listener_task.done():
        app.state.listener_task.cancel()
        logger.info("Queue 리스너 태스크를 취소했습니다.")

# --------------------------------------------------------------------------
# FastAPI 앱 생성 및 설정
# --------------------------------------------------------------------------
app = FastAPI(
    title="Smart Safety System API",
    description="컨베이어 작업 현장 스마트 안전 시스템 API (2-Process Architecture)",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처에서의 연결을 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --------------------------------------------------------------------------
# API 라우터 등록
# --------------------------------------------------------------------------
app.include_router(control_api.router, prefix="/api/control", tags=["System Control"])
app.include_router(log_api.router, prefix="/api/logs", tags=["Log Data"])
app.include_router(zone_api.router, prefix="/api/zones", tags=["Danger Zones"])
app.include_router(streaming.router, prefix="/api/streaming", tags=["Video Streaming"])
app.include_router(alert_ws.router, prefix="/ws/alerts", tags=["WebSocket (Alerts)"])
app.include_router(log_ws.router, prefix="/ws/logs", tags=["WebSocket (Log Stream)"])

# --------------------------------------------------------------------------
# 기본 및 상태 확인 라우트
# --------------------------------------------------------------------------
@app.get("/", summary="API 서버 상태 확인", tags=["Status"])
def read_root():
    return {"status": "Smart Safety System API is running"}

@app.get("/status", summary="시스템 전체 상태 조회", tags=["Status"])
def get_overall_status(request: Request):
    """시스템의 서비스 상태와 비전 워커 프로세스의 생존 여부를 반환합니다."""
    worker_process = request.app.state.worker_process
    db_service = request.app.state.db_service

    status = {
        "api_server_status": "RUNNING",
        "database_service": db_service.get_status(),
        "vision_worker_alive": worker_process.is_alive() if worker_process else False,
    }
    return status
