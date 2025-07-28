# Smart Safety System for Conveyor Worksite

## 🎯 프로젝트 목표

작업 현장에서 발생할 수 있는 ‘끼임 사고’를 방지하기 위한 스마트 안전 시스템 구축. 특히 **비정형 작업 중**에는 전원을 물리적으로 차단하여 **사람이 있는 상황에서 컨베이어벨트를 작동시키지 않도록** 하는 것이 핵심 목표.

---

## ✅ 핵심 요구사항 요약

- **비정형 작업 중**: 사람 객체가 위험 구역 내 감지되면 전원 릴레이를 차단하여 **절대 작동 불가**
- **정형 작업 중**: 사람 감지 시 속도 50% 감속 → **자세 이상, 센서 이상 감지 시 정지**
- 기존 CCTV와 센서 인프라를 활용한 **저비용 고효율** 구현
- **작업 모드(정형 / 비정형)** 자동 판단 로직 포함
- YOLOv8 기반 객체 탐지 + rule engine 기반 제어 시스템

---

## 🧱 시스템 구조 (Layer 구성)

### 1. Input Layer
- CCTV, 웹캠 → OpenCV로 실시간 프레임 수신 및 전처리
- 센서 입력 (초음파, IR 등)
- 모듈: `stream.py`, `preprocess.py`, `sensor.py`, `adapter.py`

### 2. Detection Layer
- `person_detector`: 사람 탐지 (YOLOv8)
- `pose_detector`: OpenPose 기반 자세 이상 판단
- `hand_gesture_detector`: 위험 손 모양 감지
- `danger_zone_mapper`: 지정 위험 구역 내 객체 감지
- 결과는 `detector.py`를 통해 Logic Layer에 전달

### 3. Logic Layer
- `risk_evaluator`: 위험 점수 계산
- `mode_manager`: 작업 모드 판단 (정형/비정형)
- `rule_engine`: 위험 판단 (Safe / Warn / Stop)
- 제어 명령 및 알림 분기 처리

### 4. Control Layer
- `alert_controller`: 경광등, 부저 제어
- `power_controller`: 전원 릴레이 제어
- `speed_controller`: 속도 조절
- `warning_device`: 기타 장치 제어

### 5. Interface Layer
- FastAPI 서버 + JavaScript UI
- 관리자 대시보드 제공

### 6. DB Layer
- **이벤트 로그**: 감지/판단/경고 기록 저장 (Firestore `event_logs` 컬렉션)
- **위험 구역 설정**: 다각형 위험 구역 정보 저장 (Firestore `danger_zones` 컬렉션)

---

## ⚠️ 주요 에러 및 해결된 이슈

- **(해결)** **위험 구역 데이터 관리 방식 개선**: 
    - **문제점**: 기존 `danger_zones.json` 파일은 확장성, 실시간 업데이트, 중앙 관리에 한계가 있었음.
    - **해결**: 위험 구역 정보를 **Firestore DB**에 저장하도록 시스템을 전면 개편. 이를 위해 `server` 모듈에 `ZoneService` (DB 로직), `zone_api` (API 엔드포인트), `dependencies` (의존성 주입)를 추가함. `detect/danger_zone_mapper`는 이제 `ZoneService`를 통해 DB에서 직접 구역 정보를 로드함.

- **(해결)** **Firestore 데이터 타입 불일치**: 
    - **문제점**: Firestore는 2차원 배열(`[[x,y], ...]`)을 직접 지원하지 않아, 'map의 배열'(`[{0:x, 1:y}, ...]`) 형태로 저장해야 했음. 이로 인해 Python에서 데이터를 읽어올 때 `TypeError` 발생.
    - **해결**: `danger_zone_mapper.py`의 `add_zone` 함수에 데이터 변환 로직을 추가하여, Firestore의 `map` 구조를 Python의 `list` 구조로 명시적으로 변환 후 `np.array()`에 전달함으로써 문제 해결.

- **(해결)** **Firestore 연결 난립 및 중앙화**: 
    - **문제점**: `DBService`와 `ZoneService`가 각각 `firebase_admin.initialize_app()`을 호출하여 DB 연결이 여러 곳에서 중복 발생하고 있었음.
    - **해결**: `server/app.py`의 `lifespan` 함수에서 서버 시작 시 **단 한 번만** `firebase_admin.initialize_app()`을 호출하고 `firestore.client()` 객체를 생성하여 `app.state.db`에 저장하도록 변경. 모든 서비스(`DBService`, `ZoneService`)는 이제 `app.state.db`에서 가져온 단일 DB 클라이언트 객체를 주입받아 사용함.

- **(해결)** **누락된 `get_db_service` 함수 추가**: 
    - **문제점**: `server/dependencies.py` 리팩토링 과정에서 `get_db_service` 함수가 누락되어 `app.py`에서 `ImportError` 발생.
    - **해결**: `server/dependencies.py`에 `get_db_service` 함수를 추가하여 `DBService` 인스턴스를 올바르게 주입할 수 있도록 함.

- **(해결)** **잘못된 서버 실행 위치**: 
    - **문제점**: `uvicorn` 명령어를 프로젝트 루트가 아닌 하위 디렉토리에서 실행하여 `ImportError` 발생.
    - **해결**: `uvicorn` 명령은 항상 **프로젝트의 최상위 루트 디렉토리**에서 실행해야 함을 명확히 함.

- YOLOv8 예측 결과 관련 오류 (`stream=True` → generator 반환 이슈)
- class filter 중복 체크 문제
- `VideoStream.read()` 누락 오류

---

## 📁 폴더 구조 (2025.07 기준)

```
.
├── ...
├── detect/
│   ├── ...
│   └── danger_zone_mapper.py
├── logic/
│   └── ...
├── server/
│   ├── app.py
│   ├── dependencies.py
│   ├── routes/
│   │   ├── events.py
│   │   └── zone_api.py  # <--- 추가됨
│   └── services/
│       ├── db_service.py
│       └── zone_service.py # <--- 추가됨
└── ...
```

---

## 🧭 향후 계획

- **실시간 위험 구역 업데이트**: 현재 백그라운드 워커가 DB의 위험 구역 변경 사항을 즉시 반영하지 못함. 주기적 업데이트 또는 Firestore `on_snapshot`을 이용한 이벤트 기반 업데이트 로직 구현 필요.
- **React 프론트엔드 연동**: `zone_api.py`와 연동하여, 관리자가 웹 UI에서 직접 위험 구역을 시각적으로 생성/수정/삭제하는 기능 구현.
- failsafe 로직 강화: UI 승인 없이는 절대 전원 불가 구조 고려.
- Rule Engine 방식 개선: Risk Score vs Boolean 판단.
- Unity 기반 3D 시각화 시도.

## 🧠 현재까지의 프로젝트 이해 (Gemini)

이 문서는 Gemini가 프로젝트의 현재 상태와 핵심 로직에 대해 이해하고 있는 내용을 요약합니다. 다음 세션에서 원활한 협업을 위해 지속적으로 업데이트됩니다.

### 1. 위험 구역 관리 시스템 개편 (최신 업데이트)

- **저장소**: 위험 구역 데이터의 영구 저장소가 로컬 `danger_zones.json` 파일에서 **Google Firestore**로 이전되었습니다. 이를 통해 중앙 관리, 실시간 업데이트, 확장성을 확보했습니다.
- **핵심 모듈**:
    - **`ZoneService` (`server/services/zone_service.py`)**: Firestore의 `danger_zones` 컬렉션에 대한 CRUD(Create, Read, Update, Delete) 로직을 전담합니다.
    - **`zone_api` (`server/routes/zone_api.py`)**: 외부(React 프론트엔드 등)에서 위험 구역을 관리할 수 있도록 `GET`, `POST`, `PUT`, `DELETE` API 엔드포인트를 제공합니다.
    - **`DangerZoneMapper` (`detect/danger_zone_mapper.py`)**: 이제 `ZoneService`를 통해 DB에서 직접 위험 구역 정보를 로드합니다. Firestore의 데이터 형식(`map`의 배열)을 Python에서 사용하는 `list`의 `list`로 변환하는 로직을 포함합니다.
- **데이터 형식**: Firestore에는 2차원 배열을 직접 저장할 수 없으므로, `points` 필드는 **`map`의 배열** (Array of Maps) 형태로 저장하는 것을 표준으로 정립했습니다. 각 `map`은 `{ '0': x_좌표, '1': y_좌표 }` 구조를 가집니다.

### 2. Firestore 연결 중앙화 및 의존성 관리 (최신 업데이트)

- **중앙 초기화**: `firebase_admin.initialize_app()` 호출은 이제 `server/app.py`의 `lifespan` 함수에서 서버 시작 시 **단 한 번만** 수행됩니다. 생성된 `firestore.client()` 객체는 `app.state.db`에 저장되어 애플리케이션 전반에 걸쳐 공유됩니다.
- **의존성 주입**: `server/dependencies.py`는 `app.state.db`에서 공유된 DB 클라이언트 객체를 가져와 `ZoneService`와 `DBService` 인스턴스에 주입하는 역할을 합니다. 이로써 각 서비스는 DB 연결 로직에 대해 알 필요 없이 비즈니스 로직에만 집중할 수 있습니다.
- **서비스 단순화**: `server/services/db_service.py`와 `server/services/zone_service.py`는 더 이상 자체적으로 Firebase를 초기화하거나 인증서 경로를 관리하지 않습니다. 생성자에서 이미 초기화된 `firestore.client()` 객체를 인자로 받습니다.
- **Facade 주입**: `server/app.py`에서 `ServiceFacade`와 `Detector`를 초기화할 때, 이미 생성된 `DBService` 및 `ZoneService` 인스턴스를 직접 주입합니다. 이는 Facade 계층이 필요한 서비스 인스턴스를 명확히 전달받도록 하여 결합도를 낮춥니다.

### 3. 핵심 요구사항 재정의 및 이해

*   **작업 모드 정의의 명확화**:
    *   **`operating` 모드 (정형 작업)**: 컨베이어 벨트가 현재 작동 중인 상태.
        *   목표: 위험 상황 발생 시 **감속** 또는 **정지**를 통해 사고 예방.
    *   **`stopped` 모드 (비정형 작업)**: 컨베이어 벨트가 현재 정지 중인 상태.
        *   목표: 위험 구역 내 사람 감지 또는 특정 센서 알림 시 **전원 투입을 절대적으로 방지 (LOTO 기능)**. 이는 시스템의 최우선 안전 목표입니다.
*   **센서 데이터의 중요성**: `InputAdapter`를 통해 들어오는 센서 데이터(특히 컨베이어 벨트 작동 상태)는 작업 모드 판단 및 위험 평가에 필수적인 요소입니다.

### 4. Logic Layer의 상세 역할 및 흐름 (재설계 반영)

Logic Layer는 `InputAdapter`와 `Detection Layer`로부터 받은 데이터를 기반으로 시스템의 핵심 안전 판단을 수행하며, `Control Layer`로 전달할 최종 명령을 결정합니다.

*   **`RiskEvaluator` (`logic/risk_evaluator.py`)**:
    *   **역할**: `Detection Layer`의 결과(사람, 자세, 위험 구역 침입)와 `InputAdapter`의 **센서 데이터**를 종합하여 잠재적인 위험도를 평가하고 정량화합니다.
    *   **입력**: `detection_result` (사람, 자세, 위험 구역 정보), `sensor_data` (센서 알림 상태 포함).
    *   **출력**: `risk_level` (safe, medium, high, critical) 및 `risk_score`, 상세 위험 요소 목록.

*   **`ModeManager` (`logic/mode_manager.py`)**:
    *   **역할**: 컨베이어 벨트의 현재 작동 상태를 기반으로 시스템의 작업 모드를 결정합니다.
    *   **입력**: `is_conveyor_operating` (컨베이어 작동 여부 - `InputAdapter`의 센서 데이터에서 파생).
    *   **출력**: 현재 작업 모드 (`'operating'` 또는 `'stopped'`).

*   **`RuleEngine` (`logic/rule_engine.py`)**:
    *   **역할**: `ModeManager`가 판단한 작업 모드와 `RiskEvaluator`가 평가한 위험도를 종합하여, 시스템이 취해야 할 최종 제어 명령 목록을 결정합니다.
    *   **핵심 규칙**:
        *   **IF `mode` is `'stopped'` (컨베이어 정지 상태)**:
            *   **AND** `risk_level` is not `'safe'` (위험 구역 내 사람 감지 또는 센서 알림 등):
                *   **Action**: `PREVENT_POWER_ON` (LOTO), `TRIGGER_ALARM_CRITICAL`, `LOG_LOTO_ACTIVE`.
            *   **ELSE** (`risk_level` is `'safe'`):
                *   **Action**: `ALLOW_POWER_ON`, `LOG_STOPPED_SAFE`.
        *   **IF `mode` is `'operating'` (컨베이어 작동 상태)**:
            *   **IF** `risk_level` is `'critical'` (예: 넘어짐, 심각한 자세 이상):
                *   **Action**: `STOP_POWER`, `TRIGGER_ALARM_CRITICAL`, `LOG_CRITICAL_INCIDENT`.
            *   **IF** `risk_level` is `'high'` (예: 위험 구역 침입):
                *   **Action**: `SLOW_DOWN_50_PERCENT`, `TRIGGER_ALARM_HIGH`, `LOG_HIGH_RISK`.
            *   **IF** `risk_level` is `'medium'`:
                *   **Action**: `TRIGGER_ALARM_MEDIUM`, `LOG_MEDIUM_RISK`.
            *   **ELSE** (`risk_level` is `'safe'`):
                *   **Action**: `LOG_NORMAL_OPERATION`.
    *   **공통**: 모든 위험 상황에 대해 `NOTIFY_UI` 액션 포함.

*   **`LogicFacade` (`logic/logic_facade.py`)**:
    *   **역할**: `RiskEvaluator`, `ModeManager`, `RuleEngine`의 복잡한 상호작용을 외부로부터 숨기는 통합 인터페이스.
    *   **입력**: `detection_result` (from `Detector`), `sensor_data` (from `InputAdapter`).
    *   **흐름**: `sensor_data`에서 컨베이어 작동 상태를 추출하여 `ModeManager`에 전달하고, `detection_result`와 `sensor_data`를 `RiskEvaluator`에 전달한 후, 최종적으로 `RuleEngine`을 통해 결정된 행동 목록을 반환합니다.