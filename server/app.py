import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------------------------------------------------------
# 시스템 경로 및 로깅 설정
# --------------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent.parent))
logger.remove()
logger.add(
    sys.stderr, level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
)

# --- 아키텍처 변경에 따른 임포트 수정 ---
from server.state_manager import SystemStateManager
from control.control_facade import ControlFacade
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from server.services.db_service import DBService
from server.services.zone_service import ZoneService
from server.services.websocket_service import WebSocketService
from server.background_worker import run_safety_system

# --- 라우터 임포트 ---
from server.routes import log_api, streaming, alert_ws, zone_api, control_api, log_ws

# --------------------------------------------------------------------------
# 중앙 설정 (CONFIG)
# --------------------------------------------------------------------------
CONFIG = {
    'input': {'camera_index': 0, 'mock_mode': False},
    'detector': {'person_detector': {'model_path': 'yolov8n.pt'}, 'pose_detector': {'pose_model_path': 'yolov8n-pose.pt'}},
    'control': {'mock_mode': False},
    'service': {'firebase_credential_path': str(Path(__file__).parent.parent / "config" / "firebase_credential.json")}
}

# --------------------------------------------------------------------------
# FastAPI Lifespan (서버 시작/종료 이벤트)
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 서버 시작 ---
    logger.info("FastAPI 서버 시작 프로세스를 개시합니다...")
    app.state.loop = asyncio.get_running_loop()

    # 1. Firestore DB 초기화 (에뮬레이터 감지 로직 개선)
    try:
        # FIRESTORE_EMULATOR_HOST 환경 변수가 설정되어 있으면 에뮬레이터를 사용
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            logger.warning("FIRESTORE_EMULATOR_HOST 환경 변수 감지. Firestore 에뮬레이터를 사용합니다.")
            cred = credentials.AnonymousCredentials()
            firebase_admin.initialize_app(
                credential=cred,
                options={"projectId": "smart-safety-system-emul"}
            )
            app.state.db = firestore.client()
            logger.info("Firestore 에뮬레이터에 연결되었습니다.")
        else:
            logger.info("실제 Firestore DB에 연결합니다.")
            cred_path = CONFIG['service']['firebase_credential_path']
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase 인증서 파일을 찾을 수 없습니다: {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            app.state.db = firestore.client()
        
        logger.success("Firestore 클라이언트가 성공적으로 생성되었습니다.")

    except Exception as e:
        logger.critical(f"Firestore 초기화 실패: {e}.")
        app.state.db = None

    # 2. 핵심 서비스 및 Facade 인스턴스화
    if app.state.db:
        db_client = app.state.db
        
        # 제어 계층 Facade를 먼저 생성합니다.
        app.state.control_facade = ControlFacade(mock_mode=CONFIG['control']['mock_mode'])
        logger.success("ControlFacade 초기화 완료.")

        # ControlFacade를 SystemStateManager에 주입하여 생성합니다.
        app.state.state_manager = SystemStateManager(control_facade=app.state.control_facade)
        logger.success("SystemStateManager 초기화 완료.")

        # 나머지 서비스들을 생성합니다.
        app.state.websocket_service = WebSocketService()
        app.state.db_service = DBService(db=db_client, loop=app.state.loop, websocket_service=app.state.websocket_service)
        zone_service = ZoneService(db=db_client)
        
        # 나머지 Facade들을 생성합니다.
        app.state.detector = Detector(config=CONFIG.get('detector', {}), zone_service=zone_service)
        app.state.logic_facade = LogicFacade(config=CONFIG)
        
        logger.success("모든 서비스 및 로직 모듈 초기화 완료.")

        # 4. 백그라운드 워커를 비동기 태스크로 시작
        worker_task = asyncio.create_task(run_safety_system(app))
        app.state.worker_task = worker_task
        logger.success("백그라운드 안전 시스템 워커를 비동기 태스크로 시작했습니다.")
    else:
        logger.critical("DB 연결 실패로 인해 핵심 모듈 및 워커를 시작하지 않습니다.")

    yield
    
    # --- 서버 종료 ---
    logger.info("FastAPI 서버가 종료됩니다...")
    if 'worker_task' in app.state and not app.state.worker_task.done():
        logger.info("백그라운드 워커 태스크를 취소합니다.")
        app.state.worker_task.cancel()

# --------------------------------------------------------------------------
# FastAPI 앱 생성 및 설정
# --------------------------------------------------------------------------
app = FastAPI(
    title="Smart Safety System API",
    description="컨베이어 작업 현장 스마트 안전 시스템 API",
    version="2.0.0", # 아키텍처 변경으로 메이저 버전 업데이트
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:8080"],
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
    """시스템의 논리적, 물리적, 서비스 상태를 종합하여 반환합니다."""
    state_manager = request.app.state.state_manager
    control_facade = request.app.state.control_facade
    worker = request.app.state.worker_task

    status = {
        "logical_status": state_manager.get_status(),
        "physical_status": control_facade.get_power_status(),
        "background_worker_alive": not worker.done() if worker else False,
    }
    return status