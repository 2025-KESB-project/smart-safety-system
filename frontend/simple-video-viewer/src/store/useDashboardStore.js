// src/store/useDashboardStore.js
import { create } from 'zustand';

const useDashboardStore = create((set, get) => ({
  // ───── 상태 ─────
  logs: [],              // 이벤트 로그 리스트
  zones: [],             // 위험 구역 리스트
  loading: false,        // 로딩 상태
  error: null,           // 일반 에러 메시지
  popupError: null,      // 팝업 표시용 에러 메시지
  operationMode: null,   // 컨베이어 운영 모드


  // ───── 상태 변경 액션 ─────
  addLog: (log) => set((state) => ({ logs: [log, ...state.logs] })),
  setZones: (zones) => set({ zones }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setPopupError: (popupError) => set({ popupError }),
  setOperationMode: (operationMode) => set({ operationMode }),

  // ───── API 호출 액션 ─────

  // 이벤트 로그 조회
  fetchLogs: async (showLoading = false) => {
    if (showLoading) set({ loading: true });
    set({ error: null });
    try {
      const res = await fetch('http://localhost:8000/api/logs?limit=50');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      set({ logs: data });
    } catch (e) {
      console.error(e);
      set({ error: '로그를 불러오는 중 오류가 발생했습니다.' });
    } finally {
      if (showLoading) set({ loading: false });
    }
  },

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
      set({ error: '위험 구역 목록을 불러오는 중 오류가 발생했습니다.' });
    } finally {
      set({ loading: false });
    }
  },

  // 컨베이어 제어 API
  handleControl: async (command, options = {}) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`http://localhost:8000/api/control/${command}`, {
        method: 'POST',
        ...options,
      });

      // 202 → 사용자 확인 필요
      if (res.status === 202) {
        const data = await res.json();
        if (data.confirmation_required && window.confirm(data.message)) {
          const confirmedUrl = new URL(`http://localhost:8000/api/control/${command}`);
          confirmedUrl.searchParams.append('confirmed', 'true');
          await get().handleControl(confirmedUrl.toString(), options);
        }
        return;
      }

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      set({ operationMode: data.operation_mode });

    } catch (e) {
      console.error(e);
      const errorMessage = e.message || '명령을 실행하는 중 오류가 발생했습니다.';
      set({ popupError: errorMessage });
      setTimeout(() => set({ popupError: null }), 5000);
    } finally {
      set({ loading: false });
    }
  },
}));

export default useDashboardStore;
