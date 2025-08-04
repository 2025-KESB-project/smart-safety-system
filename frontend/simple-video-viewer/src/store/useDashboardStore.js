import { create } from 'zustand';

const useDashboardStore = create((set, get) => ({
  // 1. 상태 (State)
  logs: [],
  zones: [],
  operationMode: null,
  loading: false,
  error: null,
  popupError: null,

  // 2. 액션 (Actions)

  /**
   * API에서 초기 로그 데이터를 가져옵니다.
   * @param {boolean} showLoading - 로딩 인디케이터 표시 여부
   */
  fetchLogs: async (showLoading = false) => {
    if (showLoading) set({ loading: true });
    set({ error: null });
    try {
      const res = await fetch('/api/logs?limit=50');
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

  /**
   * API에서 위험 구역 목록을 가져옵니다.
   */
  fetchZones: async () => {
    try {
      const res = await fetch('/api/zones/');
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
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
    set(state => ({ logs: [newLog, ...state.logs] }));
  },

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
  handleControl: async (controlType) => {
    set({ loading: true });
    const url = `/api/control/${controlType}`;

    try {
      const res = await fetch(url, { method: 'POST' });

      // 202 Accepted: 2차 확인 필요
      if (res.status === 202) {
        const data = await res.json();
        if (data.confirmation_required && window.confirm(data.message)) {
          const confirmedUrl = new URL(url, window.location.origin);
          confirmedUrl.searchParams.append('confirmed', 'true');
          // 재귀적으로 자기 자신을 다시 호출
          await get().handleControl(confirmedUrl.pathname + confirmedUrl.search);
        }
        return; // 2차 확인 흐름 종료
      }

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      set({ operationMode: data.operation_mode });

    } catch (e) {
      console.error(e);
      get().setPopupError(e.message || '명령을 실행하는 중 오류가 발생했습니다.');
    } finally {
      set({ loading: false });
    }
  },
}));

export default useDashboardStore;