import { create } from 'zustand';
import { logAPI, zoneAPI, controlAPI } from '../services/api';

// WebSocket 인스턴스를 React 생명주기 외부에서 관리하여 StrictMode 중복 실행 방지
let socketInstance = null;

const useDashboardStore = create((set, get) => ({
  // 1. 상태 (State)
  logs: [],
  zones: [],
  operationMode: null,
  loading: false,
  error: null,
  popupError: null,
  globalAlert: null, // 긴급 알림용 상태

  // --- LOTO 관련 상태 추가 ---
  personDetectedInMaintenance: false,
  lotoSensorOn: false,

  // --- UI 상태 ---
  activeId: null,
  isDangerMode: false,
  configAction: null,
  selectedZoneId: null,
  newZoneName: '',
  imageSize: null,
  
  wsStatus: 'closed', // 초기 상태는 'closed'
  currentTime: '',
  
  // 2. 액션 (Actions)

  initialize: async () => {
    get().connect();
    get().startTimer();
    await get().fetchLogs(true);
    await get().fetchZones();
  },

  disconnect: () => {
    if (socketInstance) {
      console.log("[WS] 외부 인스턴스 연결을 종료합니다.");
      socketInstance.close(4000, "User-initiated disconnect");
      socketInstance = null;
    }
    set({ wsStatus: 'closed' });
  },

  connect: () => {
    // React 생명주기 외부의 인스턴스를 확인하여 중복 연결을 원천적으로 차단
    if (socketInstance) {
      console.log("[WS] 외부 인스턴스가 이미 존재하여 연결을 중단합니다.");
      return;
    }

    set({ wsStatus: 'connecting' });
    console.log("[WS] 새로운 외부 인스턴스 연결을 시작합니다.");
    socketInstance = new WebSocket('ws://localhost:8000/ws/logs');

    socketInstance.onopen = () => {
      console.log("[WS] ✅ 연결 성공!");
      set({ wsStatus: 'open' });
    };

    socketInstance.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log(`[WS_MESSAGE_RECEIVED] at ${new Date().toISOString()}:`, message);

        // 1. 로그 목록에 항상 추가
        if (message && message.event_type) {
          get().addLog(message);
        }

        // 2. LOTO 상태 업데이트 로직 (백엔드 코드 기반)
        const isWarning = message.log_risk_level === 'WARNING';
        const isPersonDetected = message.details?.description?.includes('Person detected');

        if (isWarning && isPersonDetected) {
          set({ personDetectedInMaintenance: true });
          console.log("[LOTO] 위험 구역 내 사람 감지 로그 수신. personDetectedInMaintenance를 true로 설정합니다.");
        }

      } catch (e) {
        console.error("WebSocket 메시지 처리 오류:", e);
      }
    };

    socketInstance.onerror = (error) => {
      console.error("❌ WebSocket 오류 발생:", error);
      set({ wsStatus: 'error' });
    };

    socketInstance.onclose = (event) => {
      console.log(`[WS] ⛔️ 연결 닫힘. Code: ${event.code}`);
      socketInstance = null; // 인스턴스 참조 제거
      set({ wsStatus: 'closed' });
    };
  },

  startTimer: () => {
    setInterval(() => {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const date = String(now.getDate()).padStart(2, '0');
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const day = dayNames[now.getDay()];
      let h = now.getHours();
      const m = String(now.getMinutes()).padStart(2, '0');
      const ampm = h >= 12 ? 'PM' : 'AM';
      if (h > 12) h -= 12;
      if (h === 0) h = 12;
      set({ currentTime: `${year}-${month}-${date} (${day}) / ${ampm}-${h}:${m}` });
    }, 1000);
  },

  /**
   * API에서 초기 로그 데이터를 가져옵니다.
   * @param {boolean} showLoading - 로딩 인디케이터 표시 여부
   */
  fetchLogs: async (showLoading = false) => {
    if (showLoading) set({ loading: true });
    set({ error: null });
    try {
      const data = await logAPI.getLogs();
      set({ logs: data });
    } catch (e) {
      console.error(e);
      set({ error: '로그를 불러오는 중 오류가 발생했습니다.' });
    } finally {
      if (showLoading) set({ loading: false });
    }
  },

  /**
   * API에서 위험 구역 목록을 가져옵니다.
   */
  fetchZones: async () => {
    try {
      const data = await zoneAPI.getZones();
      set({ zones: data });
    } catch (e) {
      console.error('구역 조회 실패', e);
      // 구역 조회 실패는 팝업보다는 콘솔 에러로 처리
    }
  },

  /**
   * 새로운 로그를 실시간으로 추가합니다. (웹소켓용)
   * @param {object} newLog - 웹소켓으로 수신된 새로운 로그 객체
   */
  addLog: (newLog) => {
    // 1. 항상 로그 목록에는 추가합니다.
    set(state => ({ logs: [newLog, ...state.logs] }));

    // 2. 위험 등급을 확인하여 긴급 알림을 설정합니다.
    const riskLevel = newLog?.log_risk_level;
    if (riskLevel === 'CRITICAL' || riskLevel === 'HIGH') {
      set({ globalAlert: newLog });

      // 10초 후에 알림을 자동으로 닫습니다.
      setTimeout(() => {
        // 현재 알림이 방금 설정한 알림과 동일할 때만 닫습니다.
        // (그 사이에 새로운 알림이 떴을 경우를 대비)
        if (get().globalAlert?.id === newLog.id) {
          set({ globalAlert: null });
        }
      }, 10000);
    }
  },
  setActiveId: (id) => set({ activeId: id }),

  /**
   * 에러 팝업 메시지를 설정하고, 5초 후에 자동으로 지웁니다.
   * @param {string} message - 표시할 에러 메시지
   */
  setPopupError: (message) => {
    set({ popupError: message });
    setTimeout(() => set({ popupError: null }), 5000);
  },

  /**
   * 컨베이어 제어 명령을 서버에 전송합니다.
   * @param {'start_automatic' | 'start_maintenance' | 'stop'} controlType - 제어 종류
   */
  handleControl: async (controlType, confirmed = false) => {
    // --- LOTO 안전 검사 (팝업 방식) ---
    if (controlType === 'start_automatic') {
      const { operationMode, personDetectedInMaintenance, lotoSensorOn } = get();
      const isLotoEngaged = operationMode === 'MAINTENANCE' && (personDetectedInMaintenance || lotoSensorOn);

      if (isLotoEngaged) {
        const reasons = [];
        if (personDetectedInMaintenance) reasons.push("작업 공간 내 사람이 감지되었습니다.");
        if (lotoSensorOn) reasons.push("LOTO 관련 센서가 활성화 상태입니다.");
        
        const errorMessage = `LOTO 조건 위반: ${reasons.join(' ')}`;
        get().setPopupError(errorMessage);
        return; // API 호출을 중단하고 함수 종료
      }
    }

    set({ loading: true });
    try {
      let response;
      if (controlType === 'start_automatic') {
        response = await controlAPI.startAutomaticMode(confirmed);
      } else if (controlType === 'start_maintenance') {
        response = await controlAPI.startMaintenanceMode();
      } else if (controlType === 'stop') {
        response = await controlAPI.stopSystem();
      }

      if (response && response.confirmation_required) {
        if (window.confirm(response.message)) {
          await get().handleControl(controlType, true); // 재귀 호출 with confirmation
        }
        return; // 여기서 처리를 중단하고 사용자 확인을 기다립니다.
      }

      if (response) {
        set({ operationMode: response.operation_mode });
      }
    } catch (e) {
      console.error(e);
      const errorDetail = e.response?.data?.detail || e.message;
      get().setPopupError(`명령 실행 중 오류: ${errorDetail}`);
    } finally {
      set({ loading: false });
    }
  },

  // --- 위험 구역 관리 모드 ---
  enterDangerMode: () => set({ isDangerMode: true, configAction: 'view' }),
  exitDangerMode: () => set({ isDangerMode: false, configAction: null, selectedZoneId: null, newZoneName: '' }),
  setConfigAction: (action) => {
    set(state => {
      // 새로운 액션으로 전환하기 전에 상태를 정리합니다.
      const newState = { ...state, configAction: action };

      switch (action) {
        case 'create':
          // 생성 모드에서는 선택된 ID를 해제하고, 입력 필드를 비웁니다.
          newState.selectedZoneId = null;
          newState.newZoneName = '';
          break;
        case 'update':
          // 업데이트 모드에서는 기존 구역의 이름을 사용하므로 이름 필드를 비웁니다.
          if (state.selectedZoneId) {
            const selectedZone = state.zones.find(z => z.id === state.selectedZoneId);
            newState.newZoneName = selectedZone ? selectedZone.name : '';
          }
          break;
        case 'view':
          // 조회 모드에서는 선택만 해제합니다.
          newState.selectedZoneId = null;
          break;
        default:
          break;
      }
      return newState;
    });
  },
  setSelectedZoneId: (id) => set({ selectedZoneId: id, configAction: 'view' }),
  setNewZoneName: (name) => set({ newZoneName: name }),
  setImageSize: (size) => set({ imageSize: size }),

  // --- 위험 구역 CRUD 액션 ---
  handleCreateZone: async (ratioPoints) => {
    const { newZoneName, imageSize } = get();
    // 사용자가 이름을 입력하지 않으면 기본 이름 사용
    const name = newZoneName.trim() || `새 구역 ${new Date().toLocaleTimeString()}`;
    
    // 프론트엔드에서 고유 ID 생성 (백엔드 API가 ID를 받도록 설계됨)
    const newZoneId = `zone_${Date.now()}`;

    // 백엔드 모델에 맞게 좌표를 절대값으로 변환
    const points = ratioPoints.map(r => ({
      x: Math.round(r.x * (imageSize?.naturalWidth || 1)),
      y: Math.round(r.y * (imageSize?.naturalHeight || 1)),
    }));

    // 백엔드 API(POST /api/zones)로 보낼 데이터 객체
    const newZoneData = {
      id: newZoneId,
      name,
      points,
    };

    try {
      // 수정된 api.js의 createZone 함수를 호출
      await zoneAPI.createZone(newZoneData);
      await get().fetchZones(); // 성공 후 목록 새로고침
      get().exitDangerMode();   // 성공 후 설정 모드 종료
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      const errorMessage = typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail, null, 2)
        : errorDetail;
      get().setPopupError('위험 구역 생성 실패:\n' + errorMessage);
    }
  },

  handleUpdateZone: async (ratioPoints) => {
    const { selectedZoneId, imageSize, zones } = get();
    if (!selectedZoneId) return;

    const existingZone = zones.find(z => z.id === selectedZoneId);
    if (!existingZone) return;

    const points = ratioPoints.map(r => ({
      x: Math.round(r.x * (imageSize?.naturalWidth || 1)),
      y: Math.round(r.y * (imageSize?.naturalHeight || 1)),
    }));

    try {
      await zoneAPI.updateZone(selectedZoneId, { name: existingZone.name, points });
      await get().fetchZones();
      get().exitDangerMode();
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      const errorMessage = typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail, null, 2)
        : errorDetail;
      get().setPopupError('위험 구역 업데이트 실패:\n' + errorMessage);
    }
  },

  handleDeleteZone: async () => {
    const { selectedZoneId, zones } = get();
    if (!selectedZoneId) return;

    const targetName = zones.find(z => z.id === selectedZoneId)?.name || '선택된 구역';
    if (!window.confirm(`${targetName}을 삭제하시겠습니까?`)) return;

    try {
      await zoneAPI.deleteZone(selectedZoneId);
      await get().fetchZones(); // 목록 새로고침
      // 성공 후, '조회' 모드로 전환하고 선택된 ID를 초기화합니다.
      set({ configAction: 'view', selectedZoneId: null });
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      const errorMessage = typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail, null, 2)
        : errorDetail;
      get().setPopupError('위험 구역 삭제 실패: ' + errorMessage);
    }
  },

  // --- 디버깅용 액션 ---
  testLotoCondition: () => {
    set({
      operationMode: 'MAINTENANCE',
      personDetectedInMaintenance: true,
      lotoSensorOn: false,
    });
    console.log('[DEBUG] LOTO 테스트 상태로 강제 변경됨.');
  },
}));

export default useDashboardStore;
