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
    set(state => ({ logs: [newLog, ...state.logs] }));
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
    const { zones, newZoneName, imageSize } = get();
    const name = newZoneName.trim() || `Zone ${zones.length + 1}`;
    const points = ratioPoints.map(r => ({
      x: Math.round(r.x * (imageSize?.naturalWidth || 1)),
      y: Math.round(r.y * (imageSize?.naturalHeight || 1)),
    }));

    try {
      await zoneAPI.saveZones([{ name, points }]);
      await get().fetchZones(); // 목록 새로고침
      get().exitDangerMode();
    } catch (err) {
      get().setPopupError('위험 구역 생성 실패: ' + (err.response?.data?.detail || err.message));
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
      get().setPopupError('위험 구역 업데이트 실패: ' + (err.response?.data?.detail || err.message));
    }
  },

  handleDeleteZone: async () => {
    const { selectedZoneId, zones } = get();
    if (!selectedZoneId) return;
    
    const targetName = zones.find(z => z.id === selectedZoneId)?.name || '선택된 구역';
    if (!window.confirm(`${targetName}을 삭제하시겠습니까?`)) return;

    try {
      await zoneAPI.deleteZone(selectedZoneId);
      await get().fetchZones();
      get().exitDangerMode();
    } catch (err) {
      get().setPopupError('위험 구역 삭제 실패: ' + (err.response?.data?.detail || err.message));
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