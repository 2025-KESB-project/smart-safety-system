import asyncio
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
import os
from datetime import datetime

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

# --- 라우터 및 서비스 모듈 임포트 ---
from server.models.status import SystemStatusResponse
from server.routes.log_api import router as log_api_router
from server.routes.streaming import router as streaming_router
from server.routes.alert_ws import router as websocket_router
from server.routes.zone_api import router as zone_router
from server.routes.control_api import router as control_router
from server.routes.log_ws import router as log_stream_router
from server.service_facade import ServiceFacade
from server.services.db_service import DBService
from server.services.zone_service import ZoneService
from server.services.alert_service import AlertService # AlertService 임포트
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from server.background_worker import run_safety_system

# --------------------------------------------------------------------------
# 중앙 설정 (CONFIG)
# --------------------------------------------------------------------------
CONFIG = {
    'input': {'camera_index': 3, 'mock_mode': False},
    'detector': {'person_detector': {'model_path': 'yolov8n.pt'}, 'pose_detector': {'model_path': 'yolov8n-pose.pt'}},
    'control': {'mock_mode': True},
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

    # 1. Firestore DB 초기화
    cred_path = CONFIG['service']['firebase_credential_path']
    try:
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase 인증서 파일을 찾을 수 없습니다: {cred_path}")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        app.state.db = firestore.client()
        logger.success("Firestore가 성공적으로 초기화되었습니다.")
    except Exception as e:
        logger.critical(f"Firestore 초기화 실패: {e}.")
        app.state.db = None

    # 2. 핵심 서비스 및 모듈 인스턴스화
    if app.state.db:
        db_client = app.state.db
        
        # DBService는 이제 이벤트 루프(loop)를 필요로 함
        db_service = DBService(db=db_client, loop=app.state.loop)
        zone_service = ZoneService(db=db_client)
        alert_service = AlertService() # AlertService 인스턴스화
        
        # ServiceFacade는 이제 alert_service도 관리
        service_facade = ServiceFacade(db_service=db_service, alert_service=alert_service)
        
        detector = Detector(config=CONFIG.get('detector', {}), zone_service=zone_service)
        logic_facade = LogicFacade(config=CONFIG, service_facade=service_facade)
        
        # app.state에 인스턴스 저장하여 전역 공유
        app.state.db_service = db_service # 명시적으로 저장
        app.state.service_facade = service_facade
        app.state.detector = detector
        app.state.logic_facade = logic_facade
        logger.success("핵심 서비스 및 로직 모듈 초기화 완료.")

        # 3. 백그라운드 워커 스레드 시작
        worker_thread = threading.Thread(
            target=run_safety_system,
            args=(CONFIG, service_facade, detector, logic_facade, app.state.loop),
            daemon=True
        )
        worker_thread.start()
        app.state.worker_thread = worker_thread
        logger.success("백그라운드 안전 시스템 워커 스레드를 시작했습니다.")
    else:
        logger.critical("DB 연결 실패로 인해 핵심 모듈 및 워커를 시작하지 않습니다.")

    yield
    
    # --- 서버 종료 ---
    logger.info("FastAPI 서버가 종료됩니다...")

# --------------------------------------------------------------------------
# FastAPI 앱 생성 및 설정
# --------------------------------------------------------------------------
app = FastAPI(
    title="Smart Safety System API",
    description="컨베이어 작업 현장 스마트 안전 시스템 API",
    version="1.1.0", # 버전 업데이트
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
app.include_router(log_api_router) # /api/logs
app.include_router(streaming_router, prefix="/api", tags=["Video Streaming"])
app.include_router(control_router) # /api/control
app.include_router(zone_router) # /api/zones
# WebSocket 라우터들
app.include_router(websocket_router, tags=["WebSocket (Alerts)"]) # /ws/alerts
app.include_router(log_stream_router, tags=["WebSocket (Log Stream)"]) # /ws/logs

# --------------------------------------------------------------------------
# 기본 및 상태 확인 라우트
# --------------------------------------------------------------------------
@app.get("/", summary="API 서버 상태 확인", tags=["Status"])
def read_root():
    return {"status": "Smart Safety System API is running"}

@app.get("/status", summary="시스템 서비스 상태 조회", tags=["Status"], response_model=SystemStatusResponse)
def get_system_status(request: Request):
    db_service = request.app.state.db_service
    worker = request.app.state.worker_thread
    status = {
        "database_service": db_service.get_status() if db_service else {"status": "disconnected", "reason": "DB service not initialized."},
        "background_worker_alive": worker.is_alive() if worker else False
    }
    return status
