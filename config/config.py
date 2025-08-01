# config/config.py

# --- 모의 모드 설정 ---
MOCK_MODE_INPUT = False
MOCK_MODE_CONTROL = False # 실제 하드웨어 제어를 위해 False로 설정

# --- 하드웨어 설정 ---
ARDUINO_PORT = "COM9"  # 아두이노가 연결된 시리얼 포트
ARDUINO_BAUDRATE = 9600 # 아두이노와 통신할 보드레이트

# --- 탐지 모델 설정 ---
PERSON_DETECTOR_MODEL = 'yolov8n.pt'
POSE_DETECTOR_MODEL = 'yolov8n-pose.pt'
FALL_DETECTOR_MODEL = 'fall_det_1.pt'

# --- 데이터베이스 설정 ---
# Firebase 인증서 파일의 위치 (프로젝트 루트 기준)
FIREBASE_CREDENTIAL_PATH = "config/firebase_credential.json"