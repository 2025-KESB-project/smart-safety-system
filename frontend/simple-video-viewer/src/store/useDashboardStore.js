// src/store/useDashboardStore.js
import { create } from 'zustand';

const useDashboardStore = create((set, get) => ({
  // 상태
  logs: [],
  zones: [],
  loading: false,
  error: null,
  popupError: null,
  operationMode: null,

  // 액션: 상태 업데이트
  addLog: log => set(state => ({ logs: [...state.logs, log] })),
  setZones: zones => set({ zones }),
  setLoading: loading => set({ loading }),
  setError: error => set({ error }),
  setPopupError: popupError => set({ popupError }),
  setOperationMode: operationMode => set({ operationMode }),

  // 위험 구역 목록 조회
  fetchZones: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch('http://localhost:8000/api/zones/');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      set({ zones: data });
    } catch (e) {
      console.error('구역 조회 실패', e);
      set({ error: '위험 구역을 불러오는 중 오류가 발생했습니다.' });
    } finally {
      set({ loading: false });
    }
  },

  // 로그 불러오기
  fetchLogs: async (showLoading = false) => {
    set({ loading: showLoading, error: null });
    try {
      const res = await fetch('http://localhost:8000/api/logs?limit=50');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      set({ logs: data });
    } catch (e) {
      console.error('로그 조회 실패', e);
      set({ error: '로그를 불러오는 중 오류가 발생했습니다.' });
    } finally {
      set({ loading: false });
    }
  },

  // 위험 구역 생성
  createZone: async ({ id, name, points }) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch('http://localhost:8000/api/zones/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, zone_data: { name, points } }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await get().fetchZones();
    } catch (e) {
      console.error('구역 생성 실패', e);
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  // 위험 구역 수정
  updateZone: async ({ id, name, points }) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`http://localhost:8000/api/zones/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, points }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await get().fetchZones();
    } catch (e) {
      console.error('구역 업데이트 실패', e);
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  // 위험 구역 삭제
  deleteZone: async id => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`http://localhost:8000/api/zones/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await get().fetchZones();
    } catch (e) {
      console.error('구역 삭제 실패', e);
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  // 컨트롤 API 호출
  handleControl: async (endpoint, options = {}) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`http://localhost:8000/api/control/${endpoint}`, {
        method: 'POST',
        ...options,
      });
      if (res.status === 202) {
        const data = await res.json();
        if (data.confirmation_required && window.confirm(data.message)) {
          return get().handleControl(endpoint, options);
        }
        return;
      }
      if (!res.ok) {
        const errObj = await res.json().catch(() => ({}));
        throw new Error(errObj.detail || `HTTP ${res.status}`);
      }
      const json = await res.json();
      set({ operationMode: json.operation_mode });
    } catch (e) {
      console.error('컨트롤 호출 실패', e);
      set({ popupError: e.message || '명령을 실행하는 중 오류가 발생했습니다.' });
      setTimeout(() => set({ popupError: null }), 5000);
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  // 자동 모드 시작
  handleStartAutomatic: async () => {
    const { logs, fetchLogs, handleControl, setPopupError } = get();
    if (logs.some(l => ['zone_intrusion', 'fall'].includes(l.event_type))) {
      setPopupError(
        '⚠️ 위험 구역에 인원 감지 또는 낙상이 감지되어\n운전 모드로 전환할 수 없습니다.'
      );
      setTimeout(() => setPopupError(null), 3000);
      return;
    }
    await fetchLogs(false);
    await handleControl('start_automatic');
  },

  // 점검 모드 시작
  handleStartMaintenance: async () => {
    const { handleControl } = get();
    await handleControl('start_maintenance');
  },

  // 정지
  handleStop: async () => {
    const { handleControl } = get();
    await handleControl('stop');
  }
})); // 세미콜론 꼭!
