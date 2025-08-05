import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // package.json의 "proxy" 설정과 연동
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
      const response = await apiClient.get('/logs');
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
      const response = await apiClient.get('/zones');
      return response.data;
    } catch (error) {
      console.error('Error fetching zones:', error);
      throw error;
    }
  },
  /**
   * 새로운 위험 구역을 저장합니다.
   * @param {Array<Object>} zones - 저장할 위험 구역 데이터
   * @returns {Promise<Object>} 성공 메시지
   */
  saveZones: async (zones) => {
    try {
      const response = await apiClient.post('/zones', zones);
      return response.data;
    } catch (error) {
      console.error('Error saving zones:', error);
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
      const response = await apiClient.put(`/zones/${zoneId}`, zoneData);
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
      const response = await apiClient.delete(`/zones/${zoneId}`);
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
   * 시스템을 시작합니다.
   * @returns {Promise<Object>} 성공 메시지
   */
  startSystem: async () => {
    try {
      const response = await apiClient.post('/control/start');
      return response.data;
    } catch (error) {
      console.error('Error starting system:', error);
      throw error;
    }
  },
  /**
   * 시스템을 중지합니다.
   * @returns {Promise<Object>} 성공 메시지
   */
  stopSystem: async () => {
    try {
      const response = await apiClient.post('/control/stop');
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
      const response = await apiClient.get('/control/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching status:', error);
      throw error;
    }
  },
};
