import os
from pathlib import Path
from typing import Optional

class Config:
    """시스템 전역 설정"""
    
    # 기본 경로
    BASE_DIR = Path(__file__).parent
    MODELS_DIR = BASE_DIR / "models"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # 데이터베이스 설정
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safety_system.db")
    
    # 카메라 설정
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))
    CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))
    MOCK_MODE_INPUT = os.getenv("MOCK_MODE_INPUT", "False").lower() == "true"

    # AI 모델 설정
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "../yolov8n.pt")
    POSE_MODEL_PATH = os.getenv("POSE_MODEL_PATH", "../yolov8n-pose.pt")
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    PERSON_DETECTOR_MODEL_PATH = os.getenv("PERSON_DETECTOR_MODEL_PATH", "../yolov8n.pt")
    POSE_DETECTOR_MODEL_PATH = os.getenv("POSE_DETECTOR_MODEL_PATH", "../yolov8n-pose.pt")
    DANGER_ZONE_CONFIG_PATH = os.getenv("DANGER_ZONE_CONFIG_PATH", "danger_zones.json")

    # 제어 모듈 설정
    MOCK_MODE_CONTROL = os.getenv("MOCK_MODE_CONTROL", "True").lower() == "true"

    # Firebase 설정
    FIREBASE_COLLECTION_NAME = os.getenv("FIREBASE_COLLECTION_NAME", "event_logs")
    
    # GPIO 설정 (Raspberry Pi)
    GPIO_POWER_CONTROL = int(os.getenv("GPIO_POWER_CONTROL", "18"))
    GPIO_SPEED_CONTROL = int(os.getenv("GPIO_SPEED_CONTROL", "23"))
    GPIO_WARNING_LIGHT = int(os.getenv("GPIO_WARNING_LIGHT", "24"))
    GPIO_BUZZER = int(os.getenv("GPIO_BUZZER", "25"))
    
    # 안전 설정
    DANGER_ZONE_THRESHOLD = float(os.getenv("DANGER_ZONE_THRESHOLD", "0.3"))
    SAFETY_DISTANCE = float(os.getenv("SAFETY_DISTANCE", "50.0"))
    EMERGENCY_STOP_DELAY = float(os.getenv("EMERGENCY_STOP_DELAY", "1.0"))
    
    # 서버 설정
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = LOGS_DIR / "safety_system.log"
    
    # 작업 모드 설정
    WORK_MODES = {
        "NORMAL": "정형 작업 모드",
        "IRREGULAR": "비정형 작업 모드", 
        "SAFE": "안전 모드",
        "EMERGENCY": "비상 정지 모드"
    }
    
    

    @classmethod
    def create_directories(cls):
        """필요한 디렉토리들을 생성"""
        for directory in [cls.MODELS_DIR, cls.DATA_DIR, cls.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True) 