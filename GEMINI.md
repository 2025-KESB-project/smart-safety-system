# Smart Safety System for Conveyor Worksite

##  프로젝트 목표

작업 현장에서 발생할 수 있는 ‘끼임 사고’를 방지하기 위한 스마트 안전 시스템 구축. 특히 **비정형 작업 중**에는 전원을 물리적으로 차단하여 **사람이 있는 상황에서 컨베이어벨트를 작동시키지 않도록** 하는 것이 핵심 목표.

---

## ✅ 핵심 요구사항 요약

- **비정형 작업 중**: 사람 객체가 위험 구역 내 감지되면 전원 릴레이를 차단하여 **절대 작동 불가**
- **정형 작업 중**: 사람 감지 시 속도 50% 감속 → **자세 이상, 센서 이상 감지 시 정지**
- 기존 CCTV와 센서 인프라를 활용한 **저비용 고효율** 구현
- **작업 모드(정형 / 비정형)** 자동 판단 로직 포함
- YOLOv8 기반 객체 탐지 + rule engine 기반 제어 시스템

---

##  시스템 구조 (Layer 구성)
* 각 계층은 명확한 책임 분리 원칙(SRP)을 따르며, Facade 패턴을 통해 상호작용합니다.

### 1. Input Layer
- CCTV, 웹캠 → OpenCV로 실시간 프레임 수신 및 전처리
- 모듈: `input_adapter/`

### 2. Detection Layer
- `person_detector`, `pose_detector`, `danger_zone_mapper`를 통해 영상에서 위험 요소를 탐지합니다.
- 모듈: `detect/`

### 3. Logic Layer
- `risk_evaluator`, `mode_manager`, `rule_engine`을 통해 시스템의 상태와 위험도를 판단하고, 최종 행동을 결정합니다.
- 모듈: `logic/`

### 4. Control Layer
- `alert_controller`, `power_controller` 등 물리적 장치를 제어합니다. (현재는 Mock 모드)
- 모듈: `control/`

### 5. Interface Layer (FastAPI)
- **RESTful API**: 외부 시스템(UI, 관리 도구)과의 통신을 담당합니다. Pydantic 모델을 통해 모든 요청/응답 데이터의 구조를 명확히 정의합니다.
- **WebSocket API**: 실시간 로그 및 긴급 경보를 UI에 푸시(Push)합니다.
- 모듈: `server/`

### 6. DB Layer (Firestore)
- **이벤트 로그**: 모든 시스템 이벤트를 `event_logs` 컬렉션에 저장합니다.
- **위험 구역 설정**: 다각형 위험 구역 정보를 `danger_zones` 컬렉션에 저장합니다.

---

## ⚠️ 주요 에러 및 해결된 이슈

- **(해결) 서버 시작 시 `TypeError` 발생 (2025-07-31)**:
    - **문제점**: 서버 시작 시 `TypeError: PowerController.__init__() missing 1 required positional argument: 'communicator'` 에러가 발생하며 애플리케이션이 실행되지 않음.
    - **원인 분석**: `control` 계층의 리팩토링으로 `PowerController`는 `SerialCommunicator` 객체를 필수로 요구하게 되었으나, `server/app.py`에서 `ControlFacade`를 생성할 때 이 의존성을 제대로 주입해주지 않음. `ControlFacade` 역시 하위 컨트롤러들에게 `communicator`를 전달해주는 로직이 리베이스 과정에서 유실됨.
    - **해결**:
        1.  **`control/control_facade.py`**: `__init__` 메소드가 `serial_port`와 `baud_rate`를 인자로 받도록 수정. 내부에서 `SerialCommunicator` 객체를 생성하고, 이를 `PowerController`와 `SpeedController`에 명시적으로 주입하도록 코드를 복원.
        2.  **`config/config.py`**: 하드웨어 설정을 중앙에서 관리하기 위해 `ARDUINO_PORT`와 `ARDUINO_BAUDRATE` 변수 추가.
        3.  **`server/app.py`**: `lifespan`에서 `ControlFacade`를 생성할 때, `config.py`에서 정의된 포트와 보드레이트 정보를 읽어와 인자로 전달하도록 수정. 이를 통해 서버 시작 시 제어 계층의 의존성이 올바르게 해결됨.

- **(해결) 전원 ON/OFF 로직 및 시스템 활성화 상태 관리 개선 (2025-07-30)**:
    - **문제점**: 서버 시작 시 컨베이어가 OFF 상태로 시작해야 하지만, `BackgroundWorker`가 전역 함수와 변수로 구성되어 있어 초기화 및 활성화 상태 관리가 모호했음. 서버가 켜져 있는 내내 불필요하게 전원을 끄려는 시도가 반복되었음.
    - **해결**: `background_worker.py`에 `system_is_active` 전역 변수를 도입하고, `start_system()`, `stop_system()` 함수를 추가하여 시스템의 활성화 상태를 명확히 제어하도록 리팩토링 중. `run_safety_system` 메인 루프는 `system_is_active`가 `False`일 경우 대기하도록 변경하여 불필요한 자원 소모를 방지하고, `POST` 요청을 통해서만 시스템이 본격적으로 동작하도록 함.

- **(해결) 데이터 모델 불일치 문제 해결 (2025-07-29)**:
    - **문제점**: 위험 구역 좌표 데이터가 백엔드에서는 `{'0': x, '1': y}` 형태로, 프론트엔드에서는 `{'x': x, 'y': y}` 형태로 사용되어 불필요한 변환 로직과 잠재적 오류 가능성이 존재했음.
    - **해결**: 백엔드의 API와 서비스 로직을 전면 리팩토링하여, Pydantic 모델을 통해 데이터 형식을 `{'x': x, 'y': y}`로 통일함. 이를 통해 코드의 명확성과 데이터 무결성을 확보하고 프론트엔드와의 연동을 단순화함. (이후 기존 DB 데이터 삭제를 통해 완전한 해결)

- **(해결) API 구조 및 실시간 통신 시스템 전면 개선 (2025-07-28)**:
    - **문제점**: API 구조가 직관적이지 않고, 5초 폴링 방식의 비효율적인 로그 조회 시스템을 사용하고 있었음.
    - **해결**: RESTful 원칙에 따라 API 구조를 리팩토링하고, WebSocket 기반의 실시간 통신 아키텍처를 도입하여 시스템 전체의 반응성과 효율성을 극대화함. (상세 내용은 하단 Gemini 이해 섹션 참고)

---

##  폴더 구조 (2025.07-28 기준)

'''
.
├── ...
├── server/
│   ├── app.py              # FastAPI 앱 초기화 및 중앙 관리
│   ├── dependencies.py     # 의존성 주입
│   ├── models/             # Pydantic 모델 (데이터 설계도)
│   │   ├── control.py
│   │   ├── status.py
│   │   ├── websockets.py
│   │   └── zone.py
│   ├── routes/             # API 엔드포인트 정의
│   │   ├── alert_ws.py     # (구 websockets.py) 긴급 알림 WebSocket
│   │   ├── control_api.py  # 시스템 제어 API
│   │   ├── log_api.py      # (구 events.py) 과거 로그 조회 API
│   │   ├── log_ws.py       # (구 log_stream.py) 실시간 로그 WebSocket
│   │   ├── streaming.py
│   │   └── zone_api.py
│   └── services/           # 비즈니스 로직
│       ├── alert_service.py
│       ├── db_service.py   # DB 로직 + 실시간 로그 방송 기능
│       └── zone_service.py
└── ...
'''

---

##  향후 계획

- **React 프론트엔드 연동**: 개선된 API(`log_api.py`, `zone_api.py`)와 WebSocket(`log_ws.py`, `alert_ws.py`)을 프론트엔드에 완전히 통합.
- **(완료) 실시간 로그 업데이트**: 5초 폴링 방식을 WebSocket 기반 실시간 스트리밍으로 전환 완료.
- **Failsafe 로직 강화**: UI 승인 없이는 절대 전원 불가 구조 고려.
- **Rule Engine 방식 개선**: Risk Score vs Boolean 판단.

---

##  현재까지의 프로젝트 이해 (Gemini) - 2025-08-01 업데이트

이 문서는 Gemini가 프로젝트의 최신 상태와 핵심 로직에 대해 이해하고 있는 내용을 요약합니다.

### 1. 제어 계층 (`Control Layer`) 리팩토링 및 하드웨어 연동

- **`SerialCommunicator` 도입**: `SpeedController`와 `PowerController`가 시리얼 포트를 공유하며 발생할 수 있는 충돌을 원천적으로 방지하기 위해, 시리얼 통신을 전담하는 `SerialCommunicator` 클래스를 도입. 이제 모든 하드웨어 제어 명령은 이 클래스를 통해 아두이노로 전송됨.
- **`PowerController` 역할 재정의**: 기존의 논리적 상태만 관리하던 것에서, `SerialCommunicator`를 통해 릴레이 모듈에 직접 ON/OFF(`p1`/`p0`) 명령을 내리는 역할로 변경. 실제적인 전원 차단 기능을 담당하게 됨.
- **의존성 주입(DI) 구조 확립**: `server/app.py`가 시작될 때, `config.py`에서 포트 정보를 읽어 `ControlFacade`를 초기화. `ControlFacade`는 `SerialCommunicator`의 단일 인스턴스를 생성하여, 이를 `PowerController`와 `SpeedController`에 주입(Injection)하는 명확한 의존성 흐름을 확립함. 이를 통해 서버 시작 시 발생하던 `TypeError`를 해결.

### 2. 통합 테스트 (`test_struct.py`) 강화

- **`CRITICAL` 위험 시나리오 검증**: 기존에 누락되었던 '넘어짐' 상황에 대한 테스트 로직을 추가. `STOP_POWER` 액션이 감지되면 테스트가 성공적으로 종료되도록 구현하여, 시스템의 가장 중요한 안전 기능(전원 차단)을 검증할 수 있게 됨.

### 3. 시스템 아키텍처 및 데이터 흐름 이해

- **5-Step Pipeline**: (Input) → (Detection) → (Logic) → (Control) → (Execution) 으로 이어지는 명확한 5단계 파이프라인 구조를 이해하고 있음.
- **데이터 객체**: 각 계층이 `DetectionResult`, `List[Action]`, `Serial Command` 등 명확하게 정의된 데이터 객체를 통해 통신하는 핵심적인 아키텍처를 파악함.
- **'웅크림' 탐지 로직**: `PoseDetector`가 몸통의 세로 길이와 전체 키의 비율을 계산하여 '웅크림/끼임' 상태를 `high` 위험 등급으로 판단하는 구체적인 로직을 이해함. 이 정보는 `DetectionResult`에 직접 포함되지 않고, `people_in_zones` 필드에 위험 등급으로서 간접적으로 반영됨을 인지.

### 4. 주요 디버깅 및 해결 과정 (2025-08-01)

- **`AttributeError: 'SpeedController' object has no attribute 'get_status'`**: `ControlFacade`가 `SpeedController`의 상태를 조회할 때 발생. `SpeedController`의 `get_system_status` 메소드 이름을 `get_status`로 변경하여 해결.
- **모터 구동 문제 (초기 속도)**: `SpeedController`의 `current_speed_percent`가 기본값 100으로 설정되어 있어, `resume_full_speed` 호출 시 명령이 전송되지 않던 문제. `SpeedController`의 초기 `current_speed_percent`를 0으로 변경하여 해결.
- **`AttributeError: 'AlertController' object has no attribute 'get_status'`**: `ControlFacade`가 `AlertController`의 상태를 조회할 때 발생. `AlertController`에 `get_status` 메소드를 추가하여 해결.
- **`TypeError: PowerController.__init__() missing 1 required positional argument: 'communicator'`**: `ControlFacade`가 `PowerController`를 초기화할 때 `communicator`를 전달하지 않아 발생. `ControlFacade`의 `__init__` 메소드를 수정하여 `SerialCommunicator`를 생성하고 하위 컨트롤러에 주입하도록 해결.
- **`AttributeError: 'PowerController' object has no attribute 'turn_off'`**: `ControlFacade`가 `PowerController`의 `turn_off` 메소드를 호출했으나, 실제 메소드 이름은 `power_off`여서 발생. `ControlFacade`의 `execute_actions` 메소드에서 `turn_off`를 `power_off`로 수정하여 해결.
- **아두이노 응답 로그 미출력**: `SerialCommunicator`가 아두이노의 응답을 읽지 않던 문제. `send_command` 메소드에 `readline()`을 통한 응답 수신 및 로깅 로직 추가하여 해결.
- **`RuleEngine`의 반복적인 `POWER_ON`/`STOP_POWER` 명령 생성**: `LogicFacade`가 `RuleEngine`에 `current_conveyor_status`를 전달하고, `RuleEngine`은 컨베이어가 작동 중일 때만 `STOP_POWER` 명령을 생성하도록 로직을 수정하여 해결. (이전에는 `POWER_ON` 명령 반복 생성 문제도 동일한 방식으로 해결됨)
- **`ControlFacade`의 `POWER_OFF` 액션 무시**: `background_worker`가 `POWER_OFF` 액션을 보냈을 때 `ControlFacade`가 이를 알 수 없는 액션으로 처리하던 문제. `ControlFacade`의 `execute_actions` 메소드 조건문에 `action_type == "POWER_OFF"`를 추가하여 해결.
- **`stop_system` API 하드웨어 연동**: `control_api.py`의 `stop_system` 메소드가 `ControlFacade`를 통해 실제 하드웨어 전원을 차단하도록 수정.