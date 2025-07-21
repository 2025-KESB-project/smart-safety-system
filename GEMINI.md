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
- 감지/판단/경고 기록 저장
- MySQL 또는 Firebase 사용 예정

---

## ⚠️ 주요 에러 및 이슈

- YOLOv8 예측 결과 관련 오류 (`stream=True` → generator 반환 이슈)
- class filter 중복 체크 문제
- Adapter → Detector 흐름에서 `logic_callback` 처리 구조 이해 필요
- `VideoStream.read()` 누락 오류
- 테스트 시 모듈 import 에러 발생

---

## 📁 폴더 구조 (2025.07 기준)

```
.
├── input_adapter/
│   ├── stream.py
│   ├── preprocess.py
│   ├── sensor.py
│   └── adapter.py
├── detect/
│   ├── person_detector.py
│   ├── pose_detector.py
│   ├── hand_gesture_detector.py
│   └── danger_zone_mapper.py
├── logic/
│   ├── mode_manager.py
│   ├── risk_evaluator.py
│   └── rule_engine.py
├── control/
│   ├── alert_controller.py
│   ├── power_controller.py
│   ├── speed_controller.py
│   └── warning_device.py
├── server/
│   ├── app.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   └── services/
├── test/
│   └── test_input_adapter.py
```

---

## 🧭 향후 계획

- failsafe 로직 강화: UI 승인 없이는 절대 전원 불가 구조 고려
- Rule Engine 방식 개선: Risk Score vs Boolean 판단
- Unity 기반 3D 시각화 시도
- Flask → FastAPI 전환 여부 검토
- Firebase vs MySQL 선택 마무리

## 🧠 현재까지의 프로젝트 이해 (Gemini)

이 문서는 Gemini가 프로젝트의 현재 상태와 핵심 로직에 대해 이해하고 있는 내용을 요약합니다. 다음 세션에서 원활한 협업을 위해 지속적으로 업데이트됩니다.

### 1. 핵심 요구사항 재정의 및 이해

*   **작업 모드 정의의 명확화**:
    *   **`operating` 모드 (정형 작업)**: 컨베이어 벨트가 현재 작동 중인 상태.
        *   목표: 위험 상황 발생 시 **감속** 또는 **정지**를 통해 사고 예방.
    *   **`stopped` 모드 (비정형 작업)**: 컨베이어 벨트가 현재 정지 중인 상태.
        *   목표: 위험 구역 내 사람 감지 또는 특정 센서 알림 시 **전원 투입을 절대적으로 방지 (LOTO 기능)**. 이는 시스템의 최우선 안전 목표입니다.
*   **센서 데이터의 중요성**: `InputAdapter`를 통해 들어오는 센서 데이터(특히 컨베이어 벨트 작동 상태)는 작업 모드 판단 및 위험 평가에 필수적인 요소입니다.

### 2. Logic Layer의 상세 역할 및 흐름 (재설계 반영)

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
    *   **입력**: 현재 작업 모드 (`'operating'` 또는 `'stopped'`), `risk_analysis` 결과.
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

### 3. 주요 이슈 및 향후 계획 (Gemini 관점)

*   **자세 탐지 시각화 문제**: `pose_detector.py`의 `keypoints` 필터링 임계값(`conf > 0.5`)으로 인해 코 외의 관절이 표시되지 않는 문제 인지. 해결 방안으로 임계값 조정 또는 환경 개선 고려.
*   **컨베이어 작동 상태 센서 데이터**: `InputAdapter`의 `sensor_data` 내에 컨베이어 작동 상태를 나타내는 특정 키(`conveyor_operating`)가 필요하며, 현재는 임시로 가정하여 로직을 구현했음. 실제 센서 연동 시 해당 데이터 구조에 맞춰 `LogicFacade` 내의 추출 로직 수정 필요.
*   **Failsafe Controller**: 이중 안전장치로서의 `Failsafe Controller` 개념 인지. 현재 우선순위는 아니지만, 향후 구현 시 `RuleEngine`의 결정과 독립적으로 작동하는 비상 정지 로직으로 고려될 수 있음.