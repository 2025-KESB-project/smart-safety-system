import axios from 'axios';

const apiClient = axios.create({
  baseURL: '', // baseURL을 비워 둡니다.
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 로그 관련 API
 */
export const logAPI = {
  /**
   * 모든 로그를 조회합니다.
   * @returns {Promise<Array>} 로그 배열
   */
  getLogs: async () => {
    try {
      const response = await apiClient.get('/api/logs'); // 전체 경로 사용
      return response.data;
    } catch (error) {
      console.error('Error fetching logs:', error);
      throw error;
    }
  },
};

/**
 * 위험 구역 관련 API
 */
export const zoneAPI = {
  /**
   * 모든 위험 구역을 조회합니다.
   * @returns {Promise<Array>} 위험 구역 배열
   */
  getZones: async () => {
    try {
      const response = await apiClient.get('/api/zones'); // 전체 경로 사용
      return response.data;
    } catch (error) {
      console.error('Error fetching zones:', error);
      throw error;
    }
  },
  /**
   * 새로운 위험 구역을 생성합니다.
   * @param {Object} zoneData - 생성할 위험 구역 데이터 ({ id, name, points })
   * @returns {Promise<Object>} 성공 메시지
   */
  createZone: async (zoneData) => {
    try {
      // 백엔드의 create_zone 함수는 요청 본문에서 id와 zone_data를 모두 요구합니다.
      // FastAPI의 Body(alias="id") 기능 덕분에, 프론트에서는 id를 포함한 단일 객체로 보낼 수 있습니다.
      const response = await apiClient.post('/api/zones', zoneData);
      return response.data;
    } catch (error) {
      console.error('Error creating zone:', error);
      throw error;
    }
  },
  /**
   * 특정 위험 구역을 업데이트합니다.
   * @param {string} zoneId - 업데이트할 위험 구역의 ID
   * @param {Object} zoneData - 업데이트할 위험 구역 데이터
   * @returns {Promise<Object>} 성공 메시지
   */
  updateZone: async (zoneId, zoneData) => {
    try {
      const response = await apiClient.put(`/api/zones/${zoneId}`, zoneData); // 전체 경로 사용
      return response.data;
    } catch (error) {
      console.error(`Error updating zone ${zoneId}:`, error);
      throw error;
    }
  },
  /**
   * 특정 위험 구역을 삭제합니다.
   * @param {string} zoneId - 삭제할 위험 구역의 ID
   * @returns {Promise<Object>} 성공 메시지
   */
  deleteZone: async (zoneId) => {
    try {
      const response = await apiClient.delete(`/api/zones/${zoneId}`); // 전체 경로 사용
      return response.data;
    } catch (error) {
      console.error(`Error deleting zone ${zoneId}:`, error);
      throw error;
    }
  },
};

/**
 * 시스템 제어 관련 API
 */
export const controlAPI = {
  /**
   * 자동 운전 모드를 시작합니다.
   * @returns {Promise<Object>} 시스템 상태
   */
  startAutomatic: async () => {
    const response = await apiClient.post('/api/control/start_automatic'); // 전체 경로 사용
    return response.data;
  },
  /**
   * 정비 모드를 시작합니다.
   * @returns {Promise<Object>} 시스템 상태
   */
  startMaintenance: async () => {
    const response = await apiClient.post('/api/control/start_maintenance'); // 전체 경로 사용
    return response.data;
  },
  /**
   * 시스템을 중지합니다.
   * @returns {Promise<Object>} 시스템 상태
   */
  stop: async () => {
    const response = await apiClient.post('/api/control/stop'); // 전체 경로 사용
    return response.data;
  },
   /**
   * 현재 시스템 상태를 조회합니다.
   * @returns {Promise<Object>} 시스템 상태
   */
  getStatus: async () => {
    const response = await apiClient.get('/api/control/status'); // 전체 경로 사용
    return response.data;
  },
};
