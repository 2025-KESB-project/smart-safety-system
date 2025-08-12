import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // 백엔드 API 서버 주소
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
      const response = await apiClient.get('/api/logs');
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
      const response = await apiClient.get('/api/zones');
      return response.data;
    } catch (error) {
      console.error('Error fetching zones:', error);
      throw error;
    }
  },
  /**
   * 새로운 위험 구역을 생성합니다.
   * @param {Object} zoneData - 생성할 위험 구역 데이터 (id, name, points 포함)
   * @returns {Promise<Object>} 성공 메시지
   */
  createZone: async (zoneData) => {
    try {
      // POST 요청의 body에 zoneData를 전달합니다.
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
      const response = await apiClient.put(`/api/zones/${zoneId}`, zoneData);
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
      const response = await apiClient.delete(`/api/zones/${zoneId}`);
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
  startAutomaticMode: async (confirmed = false) => {
    try {
      const response = await apiClient.post('/api/control/start_automatic', null, { params: { confirmed } });
      return response.data;
    } catch (error) {
      console.error('Error starting automatic mode:', error);
      throw error;
    }
  },
  startMaintenanceMode: async () => {
    try {
      const response = await apiClient.post('/api/control/start_maintenance');
      return response.data;
    } catch (error) {
      console.error('Error starting maintenance mode:', error);
      throw error;
    }
  },
  stopSystem: async () => {
    try {
      const response = await apiClient.post('/api/control/stop');
      return response.data;
    } catch (error) {
      console.error('Error stopping system:', error);
      throw error;
    }
  },
   /**
   * 현재 시스템 상태를 조회합니다.
   * @returns {Promise<Object>} 시스템 상태
   */
  getStatus: async () => {
    try {
      const response = await apiClient.get('/api/control/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching status:', error);
      throw error;
    }
  },
  resetSystem: async () => {
    try {
      const response = await apiClient.post('/api/control/reset');
      return response.data;
    } catch (error) {
      console.error('Error resetting system:', error);
      throw error;
    }
  },
};
