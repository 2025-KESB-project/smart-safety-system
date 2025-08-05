import { create } from 'zustand';
import { logAPI, zoneAPI, controlAPI } from '../services/api';

const useDashboardStore = create((set, get) => ({
  // 1. 상태 (State)
  logs: [],
  zones: [],
  operationMode: null,
  loading: false,
  error: null,
  popupError: null,
  globalAlert: null, // 긴급 알림용 상태

  // --- UI 상태 ---
  activeId: null,
  isDangerMode: false,
  configAction: null,
  selectedZoneId: null,
  newZoneName: '',
  imageSize: null,
  
  // 2. 액션 (Actions)

  // --- 초기 데이터 로딩 ---
  initialize: async () => {
    set({ loading: true, error: null });
    try {
      const [logs, zones] = await Promise.all([
        logAPI.getLogs(),
        zoneAPI.getZones(),
      ]);
      set({ 
        logs, 
        zones, 
        activeId: logs.length > 0 ? logs[0].id : null 
      });
    } catch (e) {
      console.error("초기화 실패:", e);
      set({ error: '데이터를 불러오는 중 오류가 발생했습니다.' });
    } finally {
      set({ loading: false });
    }
  },

  // --- 로그 관련 액션 ---
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

  // --- 제어 관련 액션 ---
  handleControl: async (controlType) => {
    const { logs } = get();
    if (controlType === 'start_automatic' && logs.some(l => l.event_type === 'zone_intrusion' || l.event_type === 'fall')) {
      get().setPopupError('⚠️ 위험 구역에 인원 감지 또는 낙상이 감지되어\n운전 모드로 전환할 수 없습니다.');
      return;
    }

    set({ loading: true });
    try {
      let response;
      if (controlType === 'start_automatic') {
        response = await controlAPI.startAutomatic();
      } else if (controlType === 'start_maintenance') {
        response = await controlAPI.startMaintenance();
      } else {
        response = await controlAPI.stop();
      }
      set({ operationMode: response.operation_mode });
    } catch (e) {
      // Axios 에러 객체에서 상세 메시지 추출
      const errorMsg = e.response?.data?.detail || e.message || '명령 실행 중 오류가 발생했습니다.';
      get().setPopupError(errorMsg);
    } finally {
      set({ loading: false });
    }
  },

  // --- 위험 구역 관리 모드 ---
  enterDangerMode: () => set({ isDangerMode: true, configAction: 'view' }),
  exitDangerMode: () => set({ isDangerMode: false, configAction: null, selectedZoneId: null, newZoneName: '' }),
  setConfigAction: (action) => set({ configAction: action }),
  setSelectedZoneId: (id) => set({ selectedZoneId: id }),
  setNewZoneName: (name) => set({ newZoneName: name }),
  setImageSize: (size) => set({ imageSize: size }),

  // --- 위험 구역 CRUD 액션 ---
  handleCreateZone: async (ratioPoints) => {
    const { newZoneName, imageSize } = get();
    const name = newZoneName.trim() || `Zone ${Date.now()}`;
    const points = ratioPoints.map(r => ({
      x: Math.round(r.x * (imageSize?.naturalWidth || 1)),
      y: Math.round(r.y * (imageSize?.naturalHeight || 1)),
    }));

    // 백엔드에 보낼 데이터 객체 생성 (id 포함)
    const newZoneData = {
      id: `zone_${Date.now()}`, // 프론트에서 고유 ID 생성
      name,
      points,
    };

    try {
      await zoneAPI.createZone(newZoneData);
      await get().fetchZones(); // 목록 새로고침
      get().exitDangerMode();
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      // 에러 상세 정보가 객체나 배열일 경우, 읽기 좋은 JSON 문자열로 변환합니다.
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
      // 성공 후 상태 초기화
      set({ isDangerMode: false, configAction: null, selectedZoneId: null }); 
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      const errorMessage = typeof errorDetail === 'object' 
        ? JSON.stringify(errorDetail, null, 2)
        : errorDetail;
      get().setPopupError('위험 구역 삭제 실패:\n' + errorMessage);
    }
  },
  
  // --- 유틸리티 액션 ---
  setPopupError: (message) => {
    set({ popupError: message });
    setTimeout(() => set({ popupError: null }), 5000);
  },
  fetchZones: async () => {
    try {
      const zones = await zoneAPI.getZones();
      set({ zones });
    } catch (e) {
      console.error('구역 조회 실패', e);
    }
  },
}));

export default useDashboardStore;