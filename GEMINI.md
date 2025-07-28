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
- **자세 탐지 오탐지 문제**: '팔 벌리고 쪼그려 앉은 자세'를 '넘어짐'으로 오탐지하는 이슈 발생.
  - **원인**: BBox 비율 조건과 넘어짐 모델의 오인이 결합되어 발생.
  - **해결**: '끼임/웅크림'을 우선 판단하고, 해당 시 넘어짐 판단을 생략하는 방식으로 로직 고도화.
- 테스트 시 모듈 import 에러 발생
- **Git Stash 충돌**: `detect/pose_detector.py` 파일에서 Stash 적용 중 충돌 발생. 최종 합의된 로직을 기준으로 수동 병합하여 해결.

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
├── verify_fall_model.py
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

### 1. Detection Layer의 상세 역할 및 흐름

*   **`PersonDetector`**: `yolov8n.pt`를 사용하여 프레임 내의 모든 '사람' 객체를 탐지하고 바운딩 박스를 반환합니다.
*   **`PoseDetector`**: **2개의 모델**을 사용하여 자세를 복합적으로 분석합니다.
    1.  **`yolov8n-pose.pt`**: 사람의 주요 관절(keypoints)과 바운딩 박스를 탐지합니다.
    2.  **`fall_det_1.pt`**: '넘어짐' 상태에 특화된 모델로, 'Fall-Detected' 클래스를 탐지합니다.
*   **`_analyze_pose` (핵심 분석 로직)**: `PoseDetector` 내의 이 메서드는 오탐지를 최소화하고 정확도를 높이기 위해 **우선순위 기반 분석**을 수행합니다.
    1.  **(1순위) 끼임/웅크림 분석**:
        *   주요 관절(어깨, 엉덩이)의 위치를 기반으로 몸통의 수직 길이를 계산합니다.
        *   이 길이가 전체 바운딩 박스 높이의 **30% 미만**이면 **'끼임/웅크림(Crouching)'**으로 즉시 판정하고 분석을 종료합니다.
        *   **목적**: '팔 벌리고 쪼그려 앉은 자세'가 '넘어짐'으로 오탐지되는 것을 원천 차단합니다.
    2.  **(2순위) 넘어짐 분석**:
        *   '끼임/웅크림'이 아닐 경우에만 넘어짐 분석을 수행합니다.
        *   **`is_model_falling` AND (`is_torso_horizontal` OR `is_ratio_falling`)** 이라는 유연한 복합 조건을 사용합니다.
            *   **(필수)** `fall_det_1.pt`가 해당 인물을 'Fall-Detected'로 탐지해야 합니다.
            *   **_AND_**
            *   **(선택)** 몸통의 수직 길이가 전체 높이의 **25% 미만**으로 매우 짧거나(수평 상태), **_OR_** 바운딩 박스의 너비가 높이보다 **1.4배 이상**이어야 합니다.
        *   **목적**: 실제 넘어진 다양한 자세(앞, 뒤, 옆)는 놓치지 않으면서, 서 있는 자세와의 오탐지를 최소화합니다.

### 2. Logic Layer의 역할 (기존과 동일)

`Detection Layer`에서 정교하게 분석된 결과(`is_falling`, `is_crouching` 등)를 입력받아, 현재 작업 모드(`operating`/`stopped`)에 따라 최종 제어 명령(`STOP_POWER`, `SLOW_DOWN` 등)을 결정합니다.

### 3. 주요 이슈 및 향후 계획 (Gemini 관점)

*   **자세 탐지 로직 고도화 완료**:
    *   단순 BBox 비율 기반 로직에서 시작하여, **`모델 AND 조건`**, **`모델 AND (A OR B)`**, 최종적으로 **`우선순위 기반 분석`** 로직으로 발전시켰습니다.
    *   이 과정을 통해 `fall_det_1.pt` 모델 자체의 성능보다는, 여러 근거를 복합적으로 해석하고 예외 케이스를 처리하는 **분석 로직의 정교함**이 오탐지 방지에 더 중요하다는 것을 확인했습니다.
*   **컨베이어 작동 상태 센서 데이터 연동**: `Logic Layer`의 `ModeManager`가 정확히 동작하려면, 실제 컨베이어의 작동 상태를 나타내는 센서 데이터(`conveyor_operating`)를 `InputAdapter`를 통해 수신하고 `LogicFacade`에서 올바르게 파싱하는 작업이 필요합니다. (현재는 로직상 가정)
*   **테스트 케이스 확장**: 현재의 테스트 이미지 외에, 다양한 각도와 조명, 여러 사람이 겹치는 상황 등 더 복잡한 시나리오에 대한 테스트 케이스를 확보하여 시스템의 강건성을 검증할 필요가 있습니다.

---
## 🚀 통합 테스트 계획: 단계별 검증

가장 효율적이고 문제 파악이 쉬운 방법은 가장 말단(제어 계층)부터 거꾸로 확인해 나가는 것입니다.

---

### 1단계: 제어 계층(Control Layer) 단독 테스트

- **목표**: SpeedController가 아두이노로 속도 제어 신호를 정상적으로 보내는지 확인합니다.
- **방법**:
    1. `test/test_arduino.py`와 같은 간단한 테스트 스크립트를 만듭니다.
    2. 이 스크립트에서 `control/speed_controller.py`의 SpeedController 객체를 직접 생성합니다.
    3. `controller.set_speed(50)` 이나 `controller.set_speed(0)` 같은 메서드를 강제로 호출합니다.
    4. 실제 아두이노의 LED나 모터가 이에 반응하는지, 또는 시리얼 모니터에 예상된 값이 출력되는지 물리적으로 확인합니다.
- **이점**: 이 단계가 성공하면, 하드웨어 연결 및 제어 신호 자체에는 문제가 없음을 확신할 수 있습니다.

---

### 2단계: 로직 계층(Logic Layer) -> 제어 계층(Control Layer) 연동 테스트

- **목표**: 로직 계층이 생성한 제어 명령('SLOW_DOWN_50_PERCENT')이 제어 계층으로 잘 전달되어 실제 아두이노를 움직이는지 확인합니다.
- **방법**:
    1. 새로운 테스트 스크립트(`test/test_logic_to_control.py`)를 만듭니다.
    2. 이 스크립트에서 `logic/logic_facade.py`와 `control/control_facade.py`를 모두 임포트합니다.
    3. 가짜(mock) 탐지 데이터를 직접 만듭니다. 예를 들어:
       ```python
       mock_detection_result = {"person_in_zone": True, "is_falling": False, ...}
       mock_sensor_data = {"is_conveyor_operating": True}
       ```
    4. 이 가짜 데이터를 `logic_facade.process()`에 입력하여 제어 명령 리스트를 얻습니다.
    5. 반환된 명령 리스트(`['SLOW_DOWN_50_PERCENT', ...]`)를 `control_facade.execute()`에 전달합니다.
    6. 1단계와 마찬가지로, 실제 아두이노가 감속하는지 확인합니다.
- **이점**: 탐지 부분을 제외한, 시스템의 핵심 두뇌(로직)와 팔다리(제어)가 잘 연결되어 동작하는지 검증할 수 있습니다.

---

### 3단계: 탐지 계층(Detection Layer) -> 로직 계층(Logic Layer) 연동 테스트

- **목표**: 실제 영상에서 사람과 ROI를 탐지한 결과가 로직 계층으로 정확히 전달되는지 확인합니다.
- **방법**:
    1. `test/test_detect_to_logic.py` 와 같은 스크립트를 만듭니다.
    2. `detect/detect_facade.py`와 `logic/logic_facade.py`를 임포트합니다.
    3. 실제 카메라나 테스트 영상을 입력으로 `detect_facade.detect()`를 실행합니다.
    4. 반환된 `detection_result`를 `logic_facade.process()`에 전달합니다.
    5. `logic_facade`가 반환하는 최종 제어 명령 리스트가 예상대로 `'SLOW_DOWN_50_PERCENT'`인지 print문으로 확인합니다. (이 단계에서는 실제 아두이노 제어는 하지 않아도 됩니다.)
- **이점**: 실제 탐지 결과가 올바른 로직 판단으로 이어지는지 확인할 수 있습니다.

---

### 4단계: 전체 통합 테스트

- **목표**: 처음부터 끝까지 전체 시스템이 정상 동작하는지 최종 확인합니다.
- **방법**:
    1. `main.py` 또는 `test/test_detect_layer.py`와 같은 최상위 통합 테스트 스크립트를 실행합니다.
    2. 카메라 앞에서 사용자가 직접 위험 구역(ROI) 안으로 들어갑니다.
    3. 실제 컨베이어 벨트(또는 모터)의 속도가 줄어드는지 눈으로 최종 확인합니다.
