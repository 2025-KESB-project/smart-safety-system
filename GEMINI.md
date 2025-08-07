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

- **(해결) API 구조 및 실시간 통신 시스템 전면 개선 (2025-07-28)**:
    - **문제점**: API 구조가 직관적이지 않고, 5초 폴링 방식의 비효율적인 로그 조회 시스템을 사용하고 있었음.
    - **해결**: RESTful 원칙에 따라 API 구조를 리팩토링하고, WebSocket 기반의 실시간 통신 아키텍처를 도입하여 시스템 전체의 반응성과 효율성을 극대화함. (상세 내용은 하단 Gemini 이해 섹션 참고)

- **(해결) `TypeError` 및 `AttributeError`**:
    - **문제점**: `db_service.log_event` 호출 시 잘못된 인자 전달, `rule_engine`에서 딕셔너리가 아닌 객체에 `.keys()` 호출.
    - **해결**: `log_event` 호출 방식을 수정하고, `rule_engine`에 타입 체크 로직을 추가하여 안정성 확보.

- **(해결) `EOFError: Ran out of input`**:
    - **문제점**: `torch.load` 실행 시 모델 파일(`.pt`)을 읽지 못함. Git 작업 중 바이너리 파일이 손상된 것으로 추정.
    - **해결**: 손상된 `yolov8n-pose.pt` 파일을 삭제하고, 공식 소스에서 새로 다운로드하여 문제 해결.

- **(해결) 위험 구역 데이터 관리 방식 개선**: Firestore DB로 이전하여 확장성 및 중앙 관리 확보.
- **(해결) Firestore 연결 중앙화**: `app.py`의 `lifespan`에서 DB 연결을 중앙 관리하도록 수정.

- **(해결 중) 프론트엔드 API 및 WebSocket 통신 에러 (2025-08-04)**:
    - **문제점**:
        - HTTP API 요청 시 `404 Not Found` (프록시 `pathRewrite` 설정 오류).
        - WebSocket 연결 시 `403 Forbidden` (백엔드 CORS 설정 및 프론트엔드 프록시 설정 문제).
        - `Dashboard.jsx` 리팩토링 중 `selectedZoneId` 정의되지 않은 에러 및 JSX 구조 오류.
        - `useWebSocket` 훅의 `useEffect` 의존성 배열 문제.
    - **해결**:
        - `setupProxy.js`에서 HTTP 요청의 `pathRewrite` 옵션을 제거하여 `/api` 경로가 백엔드에 그대로 전달되도록 수정.
        - `Dashboard.jsx`의 WebSocket URL을 `ws://localhost:8000/ws/logs`로 직접 연결하도록 변경.
        - `server/app.py`의 `CORSMiddleware` `allow_origins`를 `["*"]`로 설정하여 모든 출처 허용.
        - `server/routes/log_ws.py`에서 WebSocket 연결 수락 시 `Access-Control-Allow-Origin: *` 헤더를 직접 추가하여 CORS 문제 해결 시도.
        - `Dashboard.jsx`에서 `selectedZoneId`를 `useDashboardStore`에서 올바르게 가져오도록 수정.
        - `Dashboard.jsx`의 JSX 구조 오류 및 `useEffect`/`useCallback` 의존성 배열 문제 해결.

- **(해결) API 호출 시 무한 로딩 및 gRPC 충돌 (2025-08-05)**:
    - **문제점**: '운전 시작' 등 API 호출 시 무한 로딩이 발생하고 gRPC 관련 경고가 반복됨. 이는 API 핸들러가 응답을 위해 시스템 상태를 조회하는 과정에서 동기적인 시리얼 통신(아두이노)이 발생하여 FastAPI 이벤트 루프를 블로킹하고, 이로 인해 백그라운드의 gRPC 통신과 교착 상태(deadlock)가 발생했기 때문.
    - **해결**: `SystemStateManager`가 물리적 장치(컨베이어 전원, 속도, 경광등)의 상태를 내부적으로 캐시하도록 변경. API 요청 시에는 시리얼 통신 없이 캐시된 상태를 즉시 반환하도록 수정. 백그라운드 워커가 제어 명령을 실행할 때만 `SystemStateManager`의 상태 업데이트 메서드를 호출하여 캐시를 동기화하도록 함. `control_api.py`에서 `worker_task.done()` 호출을 제거하고 `state_manager.is_active()`를 사용하도록 변경하여 gRPC 충돌 가능성을 제거함.

---

## 📁 폴더 구조 (2025.08-04 기준)

```
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
├── frontend/
│   ├── simple-video-viewer/
│   │   ├── src/
│   │   │   ├── App.css
│   │   │   ├── App.js
│   │   │   ├── index.css
│   │   │   ├── index.js
│   │   │   ├── reportWebVitals.js
│   │   │   ├── setupProxy.js
│   │   │   ├── assets/             # 이미지, 비디오 등 정적 자산
│   │   │   ├── hooks/              # 재사용 가능한 React 훅
│   │   │   │   └── useWebSocket.jsx
│   │   │   ├── pages/              # 라우팅되는 최상위 페이지 컴포넌트
│   │   │   │   ├── Intro/
│   │   │   │   ├── Login/
│   │   │   │   └── Dashboard/      # (리팩토링 후 컨테이너 역할만 수행)
│   │   │   │       └── Dashboard.jsx
│   │   │   ├── components/         # 재사용 가능한 UI 컴포넌트
│   │   │   │   ├── dashboard/      # Dashboard 페이지 전용 컴포넌트
│   │   │   │   │   ├── ConveyorMode.jsx
│   │   │   │   │   ├── DangerZoneSelector.jsx
│   │   │   │   │   ├── LiveStreamContent.jsx
│   │   │   │   │   ├── VideoLogTable.jsx
│   │   │   │   │   ├── ZoneConfigPanel.jsx
│   │   │   │   │   └── ZoneOverlay.jsx
│   │   │   │   └── ... (기타 공용 컴포넌트)
│   │   │   ├── services/           # 외부 API 통신 로직
│   │   │   │   └── api.js
│   │   │   ├── store/              # 중앙 상태 관리 (Zustand)
│   │   │   │   └── useDashboardStore.js
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

**🗑️ 삭제 예정 파일/폴더:**
- `frontend/simple-video-viewer/src/services/websocketService.js` (더 이상 사용되지 않음)
- `frontend/simple-video-viewer/src/assets/style.css` (더 이상 사용되지 않음)
- `frontend/simple-video-viewer/src/pages/main/` 폴더 전체 (라우팅 역할이 `App.js`로 통합됨)
- `frontend/src/pages/` 폴더 전체 (오래된 파일, 리액트 프로젝트 구조에 포함되지 않음)

---

## 🧭 향후 계획

- **React 프론트엔드 연동**: 개선된 API(`log_api.py`, `zone_api.py`)와 WebSocket(`log_ws.py`, `alert_ws.py`)을 프론트엔드에 완전히 통합.
- **(완료) 실시간 로그 업데이트**: 5초 폴링 방식을 WebSocket 기반 실시간 스트리밍으로 전환 완료.
- **Failsafe 로직 강화**: UI 승인 없이는 절대 전원 불가 구조 고려.
- **Rule Engine 방식 개선**: Risk Score vs Boolean 판단.
- **(진행 중) 프론트엔드 UI/UX 개선**: 리팩토링된 구조를 바탕으로 각 컴포넌트의 디자인 및 사용자 경험 개선.
- **(계획) 테스트 코드 작성**: 리팩토링된 컴포넌트 및 스토어 액션에 대한 단위/통합 테스트 추가.

---

## 🧠 현재까지의 프로젝트 이해 (Gemini) - 2025-08-04 업데이트

이 문서는 Gemini가 프로젝트의 최신 상태와 핵심 로직에 대해 이해하고 있는 내용을 요약합니다.

### 1. API 및 실시간 통신 시스템 전면 개선

최근 세션을 통해 서버의 API 구조와 통신 방식이 대대적으로 개선되었습니다.

#### 1.1. RESTful API 설계 및 Pydantic 모델 전면 도입

- **역할 기반 분리**: API의 역할과 책임에 따라 파일과 경로를 명확하게 분리했습니다.
    - `events.py` → `log_api.py` (`/api/logs`): 과거 로그 조회 (HTTP)
    - `streaming.py`에서 제어 기능 분리 → `control_api.py` (`/api/control`): 컨베이어 제어
- **멱등성 보장**: `toggle` 방식의 API를 명시적인 `start`, `stop`으로 변경하여, 반복 호출 시에도 동일한 결과를 보장하는 안정적인 API를 구현했습니다.
- **Pydantic 모델 적용**: 모든 주요 API(`logs`, `zones`, `control`, `status`)의 요청(Request) 및 응답(Response)을 Pydantic 모델로 엄격하게 정의했습니다.
    - **장점 1 (자동 문서화)**: `/docs`의 API 문서가 매우 상세하고 명확해졌습니다.
    - **장점 2 (데이터 안정성)**: 잘못된 형식의 데이터가 오고 가는 것을 원천적으로 차단합니다.

#### 1.2. 실시간 통신 아키텍처 구축 (WebSocket 도입)

기존의 5초 주기 폴링(Polling) 방식을 완전히 폐기하고, WebSocket을 이용한 진정한 실시간 통신 아키텍처를 구축했습니다.

- **"초기 로딩(HTTP) + 실시간 업데이트(WebSocket)" 모델**:
    - **초기 로딩**: UI가 처음 열릴 때 `GET /api/logs`를 호출하여 과거 로그를 가져옵니다.
    - **실시간 업데이트**: 이후 발생하는 모든 이벤트는 WebSocket을 통해 서버가 즉시 UI로 푸시(Push)합니다.
- **채널 분리**: 목적에 따라 두 개의 독립된 WebSocket 채널을 운영합니다.
    - **`/ws/logs` (`log_ws.py`)**: 모든 종류의 시스템 로그를 실시간으로 스트리밍하는 '뉴스 채널'.
    - **`/ws/alerts` (`alert_ws.py`)**: 긴급 상황만 전송하는 '재난 문자 채널'.
- **데이터 일관성**: `DBService`가 Firestore에 로그를 저장하는 즉시, 해당 로그를 `/ws/logs` 채널로 방송하도록 구현하여 DB와 UI 간의 데이터 일관성을 보장합니다.

### 2. Firestore 연결 및 데이터 관리

- **중앙 관리**: `app.py`의 `lifespan` 이벤트를 통해 서버 시작 시 단 한 번만 Firestore 연결을 초기화하고, 생성된 클라이언트 객체를 `app.state`를 통해 전역적으로 공유합니다.
- **데이터 모델**: `zone_api.py`는 Firestore의 데이터 구조(map의 배열)와 Python의 Pydantic 모델 간의 데이터 변환을 처리하여, 일관된 데이터 형식을 유지합니다.

### 3. 프론트엔드 아키텍처 리팩토링 (2025-08-04)

프론트엔드 코드의 유지보수성 및 확장성 강화를 위해 대대적인 리팩토링을 진행했습니다.

- **폴더 구조 재정비**:
    - `pages/`: 라우팅되는 최상위 페이지 컴포넌트 (예: `Dashboard.jsx`, `Login.jsx`).
    - `components/`: 재사용 가능한 UI 컴포넌트. 특히 `components/dashboard/` 폴더를 신설하여 `Dashboard` 페이지 전용 컴포넌트들을 모듈화했습니다.
    - `hooks/`: 재사용 가능한 로직을 담은 커스텀 React 훅 (`useWebSocket.jsx`).
    - `services/`: 외부 API 통신 로직을 담당 (`api.js`).
    - `store/`: Zustand를 활용한 중앙 상태 관리 (`useDashboardStore.js`).
- **`Dashboard.jsx` 간소화**:
    - 기존의 거대 컴포넌트였던 `Dashboard.jsx`를 순수하게 페이지 레이아웃을 담당하는 컨테이너 컴포넌트로 변경했습니다.
    - 모든 상태 관리 및 비즈니스 로직은 `useDashboardStore.js`로 이전되었습니다.
- **`useDashboardStore.js` 확장**:
    - `Dashboard.jsx`가 관리하던 대부분의 UI 상태(예: `isDangerMode`, `configAction`)와 비즈니스 로직(예: 위험 구역 CRUD, 제어 명령)을 `useDashboardStore`로 통합하여 단일 진실 공급원(Single Source of Truth) 역할을 강화했습니다.
    - API 연동을 `fetch`에서 `axios` 기반의 `services/api.js` 함수들로 전환하여 일관성과 에러 처리 효율성을 높였습니다.

### 4. 통신 문제 해결 과정 (2025-08-04)

프론트엔드와 백엔드 간의 통신 안정화를 위해 여러 문제점을 진단하고 해결했습니다.

- **HTTP API `404 Not Found` 에러**:
    - **원인**: `setupProxy.js`의 HTTP 프록시 설정에서 `pathRewrite` 옵션이 잘못 적용되어, 프론트엔드에서 `/api/logs`로 요청한 경로가 백엔드에 `/logs`로 전달되어 발생. 백엔드는 `/api/logs` 경로만 인식.
    - **해결**: `setupProxy.js`에서 `/api` 경로에 대한 `pathRewrite` 옵션을 제거하여, 프록시가 `/api` 접두사를 그대로 유지한 채 백엔드로 요청을 전달하도록 수정.
- **WebSocket `403 Forbidden` 에러**:
    - **원인**: 프론트엔드 개발 서버(`localhost:3000`)에서 백엔드 서버(`localhost:8000`)로 직접 WebSocket 연결을 시도할 때, 백엔드 FastAPI 서버의 CORS 정책에 의해 연결이 거부됨.
    - **해결**:
        1.  `Dashboard.jsx`의 WebSocket URL을 `ws://localhost:8000/ws/logs`로 직접 연결하도록 변경.
        2.  백엔드 `server/app.py`의 `CORSMiddleware` `allow_origins`를 `["*"]`로 설정하여 모든 출처에서의 연결을 허용.
        3.  (추가 시도) `server/routes/log_ws.py`의 `websocket_log_endpoint` 함수 내에서 WebSocket 연결 수락 시 `Access-Control-Allow-Origin: *` 헤더를 직접 추가하여 CORS 문제 해결 시도.
- **프론트엔드 내부 오류**:
    - **원인**: `Dashboard.jsx` 리팩토링 과정에서 `useDashboardStore`의 `selectedZoneId` 상태를 컴포넌트에서 가져오지 않아 `no-undef` 에러 발생. 또한, `useEffect` 및 `useCallback` 훅의 의존성 배열에 `useDashboardStore`의 함수를 잘못 포함하여 불필요한 재실행 및 오류 발생. JSX 구조의 중괄호 누락으로 인한 렌더링 오류.
    - **해결**:
        1.  `Dashboard.jsx`에서 `selectedZoneId`를 `useDashboardStore`로부터 올바르게 구조 분해 할당하여 가져오도록 수정.
        2.  `useEffect` 및 `useCallback`의 의존성 배열에서 `useDashboardStore`의 함수를 제거하고, 필요한 경우 `useDashboardStore.getState()`를 사용하여 스토어 상태에 접근하도록 수정.
        3.  `Dashboard.jsx`의 JSX 구조에서 누락된 닫는 태그를 추가하여 렌더링 오류 해결.
        4.  `LiveStreamContent`와 `ZoneOverlay`가 올바르게 겹쳐 보이도록 JSX 구조를 `div`로 감싸고 `position: relative` 스타일 적용.