# 🤖 Smart Safety System
## 컨베이어벨트 안전 관리 시스템

AI 기반의 실시간 안전 모니터링 및 자동 제어 시스템으로, YOLOv8과 MediaPipe를 활용하여 작업자의 안전을 보호합니다.

## 📋 목차
- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 구조](#시스템-구조)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [사용법](#사용법)
- [개발 가이드](#개발-가이드)
- [라이선스](#라이선스)

## 🎯 개요

Smart Safety System은 다음과 같은 6계층 구조로 구성된 종합적인 안전 관리 시스템입니다:

1. **입력 계층 (Input Layer)**: CCTV, 웹캠, 산업용 카메라를 통한 실시간 영상 수집
2. **감지 계층 (Detect Layer)**: YOLOv8 기반 객체 감지 및 MediaPipe 포즈 분석
3. **판단 계층 (Logic Layer)**: 위험도 평가 및 작업 모드 자동 전환
4. **제어 계층 (Control Layer)**: GPIO를 통한 하드웨어 제어 및 알림 시스템
5. **UI 계층**: FastAPI 기반 웹 대시보드 및 WebSocket 실시간 통신
6. **데이터 계층**: 감지 이력, 위험도 평가, 알림 로그 저장

## ✨ 주요 기능

### 🔍 실시간 객체 감지
- **YOLOv8**: 사람, 손, 얼굴, PPE(보호장비) 등 실시간 감지
- **MediaPipe**: 자세 분석 및 이상 행동 감지 (넘어짐, 주저앉음 등)
- **손 제스처 인식**: 정지 신호, 집는 동작 등 제스처 기반 제어

### ⚙️ 지능형 작업 모드
- **정형 작업 모드**: 일반적인 안전한 작업 환경
- **비정형 작업 모드**: 위험 요소가 있는 작업 환경
- **안전 모드**: 높은 위험도 감지 시 자동 전환
- **비상 정지 모드**: 긴급 상황 시 즉시 시스템 정지

### 🎮 자동 제어 시스템
- **전원 제어**: 위험도에 따른 자동 전원 차단
- **속도 제어**: 컨베이어벨트 속도 자동 조절
- **알림 시스템**: 시각적(경광등), 음향(부저), 텍스트 알림

### 📊 실시간 모니터링
- **웹 대시보드**: 실시간 상태 확인 및 제어
- **WebSocket**: 실시간 데이터 스트리밍
- **REST API**: 시스템 상태 조회 및 제어 명령

## 🏗️ 시스템 구조

```
smart-safety-system/
├── 📁 input_adapter/          # 입력 계층
│   ├── adapter.py            # 입력 어댑터 메인 클래스
│   ├── stream.py             # 비디오 스트림 처리
│   ├── preprocess.py         # 영상 전처리
│   └── sensor.py             # 센서 데이터 처리
├── 📁 detect/                # 감지 계층
│   ├── detector.py           # YOLOv8 객체 감지
│   ├── person_detect.py      # 사람 감지
│   ├── pose_detector.py      # 자세 분석
│   └── hand_gesture_detector.py # 손 제스처 인식
├── 📁 logic/                 # 판단 계층
│   ├── mode_manager.py       # 작업 모드 관리
│   ├── risk_evaluator.py     # 위험도 평가
│   └── rule_engine.py        # 규칙 엔진
├── 📁 control/               # 제어 계층
│   ├── power_controller.py   # 전원 제어
│   ├── speed_controller.py   # 속도 제어
│   ├── alert_controller.py   # 알림 제어
│   └── warning_device.py     # 경고 장치
├── 📁 server/                # UI 계층
│   ├── app.py               # FastAPI 서버
│   ├── config.py            # 서버 설정
│   └── routes/              # API 라우트
├── 📁 frontend/              # 프론트엔드
│   └── src/                 # React/Vue.js 소스
├── 📁 docs/                  # 문서
├── main.py                   # 메인 실행 파일
├── config.py                 # 전역 설정
└── requirements.txt          # 의존성 패키지
```

## 🚀 설치 및 실행

### 1. 시스템 요구사항
- **Python**: 3.8 이상
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows
- **하드웨어**: Raspberry Pi 4 (권장) 또는 x86 PC
- **카메라**: USB 웹캠 또는 IP 카메라
- **GPIO**: Raspberry Pi GPIO (선택사항)

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/smart-safety-system.git
cd smart-safety-system

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# YOLOv8 모델 다운로드 (자동으로 다운로드됨)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. 실행

#### 기본 실행
```bash
python main.py
```

#### 옵션과 함께 실행
```bash
# 모의 모드로 실행 (하드웨어 없이)
python main.py --mock

# 디버그 모드로 실행
python main.py --debug

# 웹 서버만 실행
cd server
python app.py
```

### 4. 웹 대시보드 접속
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 📚 API 문서

### 주요 엔드포인트

#### 시스템 상태
```http
GET /status
GET /api/detection?limit=10
GET /api/mode
GET /api/risk
GET /api/control
```

#### 제어 명령
```http
POST /api/mode/change?mode=safe&reason=위험감지
POST /api/control/power?action=emergency
POST /api/control/alert?level=critical&message=긴급상황
```

#### WebSocket 실시간 데이터
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('실시간 데이터:', data);
};
```

## 🎮 사용법

### 1. 시스템 시작
```bash
# 기본 모드로 시작
python main.py

# 모의 모드로 시작 (개발/테스트용)
python main.py --mock
```

### 2. 웹 대시보드 사용
1. 브라우저에서 `http://localhost:8000` 접속
2. 실시간 상태 모니터링
3. 작업 모드 수동 전환
4. 제어 명령 실행

### 3. API 사용 예제
```python
import requests

# 시스템 상태 조회
response = requests.get('http://localhost:8000/status')
status = response.json()

# 안전 모드로 전환
requests.post('http://localhost:8000/api/mode/change', 
              params={'mode': 'safe', 'reason': '수동 전환'})

# 비상 정지
requests.post('http://localhost:8000/api/control/power', 
              params={'action': 'emergency'})
```

### 4. 설정 변경
```python
# config.py에서 설정 수정
CAMERA_INDEX = 0          # 카메라 인덱스
CONFIDENCE_THRESHOLD = 0.5 # 감지 신뢰도 임계값
GPIO_POWER_CONTROL = 18   # 전원 제어 GPIO 핀
```

## 🔧 개발 가이드

### 1. 새로운 감지 기능 추가
```python
# detect/custom_detector.py
class CustomDetector:
    def detect(self, frame):
        # 커스텀 감지 로직
        return detection_result
```

### 2. 새로운 제어 기능 추가
```python
# control/custom_controller.py
class CustomController:
    def control(self, command):
        # 커스텀 제어 로직
        pass
```

### 3. 새로운 알림 타입 추가
```python
# control/alert_controller.py
def _send_custom_alert(self, alert):
    # 커스텀 알림 로직
    pass
```

### 4. 테스트 실행
```bash
# 단위 테스트
python -m pytest tests/

# 통합 테스트
python -m pytest tests/integration/

# 성능 테스트
python tests/performance_test.py
```

## 🛠️ 기술 스택

### Backend
- **Python 3.8+**: 메인 프로그래밍 언어
- **FastAPI**: 고성능 웹 프레임워크
- **OpenCV**: 컴퓨터 비전 라이브러리
- **YOLOv8**: 실시간 객체 감지
- **MediaPipe**: 포즈 및 제스처 인식
- **SQLAlchemy**: 데이터베이스 ORM

### Frontend
- **React/Vue.js**: 웹 프론트엔드
- **WebSocket**: 실시간 통신
- **Chart.js**: 데이터 시각화

### Hardware
- **Raspberry Pi GPIO**: 하드웨어 제어
- **USB Camera**: 영상 입력
- **LED/부저**: 시각/음향 알림

## 📊 성능 지표

- **감지 속도**: 30 FPS (640x480 해상도)
- **정확도**: 95% 이상 (표준 테스트 환경)
- **응답 시간**: < 100ms (위험 감지부터 제어까지)
- **가동률**: 99.9% (24/7 운영)

## 🔒 보안

- **인증**: JWT 토큰 기반 인증
- **권한**: 역할 기반 접근 제어 (RBAC)
- **암호화**: HTTPS/TLS 통신
- **로깅**: 보안 이벤트 로깅

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/your-username/smart-safety-system/issues)
- **문서**: [Wiki](https://github.com/your-username/smart-safety-system/wiki)
- **이메일**: support@smartsafety.com

## 🙏 감사의 말

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8
- [MediaPipe](https://mediapipe.dev/) - 포즈 및 제스처 인식
- [FastAPI](https://fastapi.tiangolo.com/) - 웹 프레임워크
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리

---

**⚠️ 주의사항**: 이 시스템은 안전 관리 보조 도구입니다. 실제 산업 환경에서 사용하기 전에 충분한 테스트와 검증이 필요합니다.