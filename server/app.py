import asyncio
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 임포트
from loguru import logger

# --------------------------------------------------------------------------
# 시스템 경로 및 로깅 설정
# --------------------------------------------------------------------------
# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 다른 모듈보다 먼저 로거 설정
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
)

from server.routes.events import event_router
from server.routes.streaming import router as streaming_router
from server.routes.websockets import router as websocket_router
# from server.routes.users import router as users_router # 존재하지 않으므로 주석 처리 또는 삭제
from server.service_facade import ServiceFacade
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from server.background_worker import run_safety_system

# --------------------------------------------------------------------------
# 중앙 설정 (CONFIG)
# --------------------------------------------------------------------------
CONFIG = {
    'input': {
        'camera_index': 3,
        'mock_mode': False
    },
    'detector': {
        'person_detector': {'model_path': 'yolov8n.pt'},
        'pose_detector': {'model_path': 'yolov8n-pose.pt'},
        'danger_zone_mapper': {'zone_config_path': 'danger_zones.json'}
    },
    'control': {
        'mock_mode': True
    },
    'service': {
        'db_service': {
            'firebase_credentials_path': str(Path(__file__).parent.parent / "config" / "firebase_credential.json"),
            'collection_name': 'event_logs'
        }
    }
}

# --------------------------------------------------------------------------
# FastAPI Lifespan 이벤트 핸들러
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 서버 시작 (Startup) ---
    logger.info("FastAPI 서버 시작 프로세스를 개시합니다...")

    # 1. 핵심 모듈 인스턴스화
    service_facade = ServiceFacade(config=CONFIG.get('service', {}))
    detector = Detector(config=CONFIG.get('detector', {}))
    logic_facade = LogicFacade(config=CONFIG, service_facade=service_facade)
    
    # 2. app.state에 인스턴스 저장하여 전역적으로 공유
    app.state.service_facade = service_facade
    app.state.detector = detector
    app.state.logic_facade = logic_facade
    logger.success("핵심 서비스 및 로직 모듈 초기화 완료.")

    # 3. 백그라운드 워커 스레드에서 사용할 asyncio 루프 저장
    app.state.loop = asyncio.get_running_loop()

    # 4. 백그라운드 워커 스레드 시작
    worker_thread = threading.Thread(
        target=run_safety_system,
        args=(CONFIG, service_facade, detector, logic_facade, app.state.loop),
        daemon=True  # 메인 스레드 종료 시 함께 종료
    )
    worker_thread.start()
    app.state.worker_thread = worker_thread
    logger.success("백그라운드 안전 시스템 워커 스레드를 시작했습니다.")
    
    yield
    
    # --- 서버 종료 (Shutdown) ---
    logger.info("FastAPI 서버 종료 프로세스를 시작합니다...")
    # 현재는 별도의 정리 로직이 없지만, 필요시 여기에 추가 (예: worker_thread.join())
    logger.info("서버가 성공적으로 종료되었습니다.")

# --------------------------------------------------------------------------
# FastAPI 앱 생성
# --------------------------------------------------------------------------
app = FastAPI(
    title="Smart Safety System API",
    description="컨베이어 작업 현장 스마트 안전 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# --------------------------------------------------------------------------
# CORS 미들웨어 설정
# --------------------------------------------------------------------------
# 허용할 출처(Origin) 목록입니다. React 개발 서버의 기본 주소인 3000번 포트를 추가합니다.
origins = [
    "http://localhost",
    "http://localhost:3000", # React 개발 서버
    "http://localhost:8080", # Vue 개발 서버 등
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 위에서 정의한 출처 목록을 허용
    allow_credentials=True, # 쿠키를 포함한 요청을 허용
    allow_methods=["*"],    # 모든 HTTP 메소드(GET, POST 등)를 허용
    allow_headers=["*"],    # 모든 HTTP 헤더를 허용
)

# --------------------------------------------------------------------------
# API 라우터 등록
# --------------------------------------------------------------------------
app.include_router(event_router, prefix="/api", tags=["Event Logs"])
app.include_router(streaming_router, prefix="/api", tags=["Streaming & Control"])
app.include_router(websocket_router) # WebSocket은 prefix나 tag가 필요 없을 수 있습니다.
# app.include_router(users_router, prefix="/api", tags=["Users"]) # 존재하지 않으므로 주석 처리 또는 삭제

# --------------------------------------------------------------------------
# 기본 라우트 (예: 상태 확인)
# --------------------------------------------------------------------------
@app.get("/", summary="API 서버 상태 확인", tags=["Status"])
def read_root():
    return {"status": "Smart Safety System API is running"}

@app.get("/status", summary="시스템 서비스 상태 조회", tags=["Status"])
def get_system_status(request: Request):
    """
    DB 서비스 등 백엔드 서비스의 현재 상태를 반환합니다.
    """
    sf: ServiceFacade = request.app.state.service_facade
    status = {
        "database_service": sf.db_service.get_status(),
        "background_worker_alive": app.state.worker_thread.is_alive()
    }
    return status

# FastAPI 서버 실행 명령어:
# uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
