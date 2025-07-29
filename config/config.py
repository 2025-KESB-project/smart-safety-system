
import os
from pathlib import Path

class AppConfig:
    """시스템 전역 설정을 담는 클래스"""

    # --- 기본 경로 설정 ---
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOGS_DIR = BASE_DIR / "logs"

    # --- 서버 설정 ---
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # --- 로깅 설정 ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = LOGS_DIR / "safety_system.log"

    # --- 입력 소스 설정 (카메라 등) ---
    INPUT_CONFIG = {
        "camera_index": int(os.getenv("CAMERA_INDEX", "0")),
        "mock_mode": os.getenv("MOCK_MODE_INPUT", "False").lower() == "true"
    }

    # --- 탐지 계층 설정 (AI 모델) ---
    DETECTION_CONFIG = {
        "person_model_path": os.getenv("PERSON_DETECTOR_MODEL_PATH", str(BASE_DIR / 'yolov8n.pt')),
        "pose_model_path": os.getenv("POSE_DETECTOR_MODEL_PATH", str(BASE_DIR / 'yolov8n-pose.pt')),
        "fall_model_path": os.getenv("FALL_DETECTOR_MODEL_PATH", str(BASE_DIR / 'fall_det_1.pt')),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.6")),
        "danger_zone_config_path": os.getenv("DANGER_ZONE_CONFIG_PATH", str(BASE_DIR / 'danger_zones.json'))
    }

    # --- 제어 계층 설정 (아두이노, GPIO 등) ---
    CONTROL_CONFIG = {
        "mock_mode": os.getenv("MOCK_MODE_CONTROL", "False").lower() == "true",
        "arduino_port": os.getenv("ARDUINO_PORT", "COM9"), # COM9 포트 명시
        "baudrate": int(os.getenv("BAUDRATE", "9600")),
        "power_gpio_pin": int(os.getenv("GPIO_POWER_CONTROL", "18"))
    }

    # --- 데이터베이스 설정 (Firebase) ---
    # 주의: Firebase 초기화를 위해서는 별도의 서비스 계정 키 JSON 파일이 필요합니다.
    # 실제 배포 시에는 환경 변수 등을 통해 경로를 안전하게 관리해야 합니다.
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

    @classmethod
    def initialize(cls):
        """설정에 필요한 디렉토리 생성 등 초기화 작업을 수행"""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"로그 디렉토리 생성/확인: {cls.LOGS_DIR}")

# logger 임포트는 설정 클래스 정의 후에 수행 (순환 참조 방지)
from loguru import logger
