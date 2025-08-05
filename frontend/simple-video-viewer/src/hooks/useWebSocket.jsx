// src/hooks/useWebSocket.js
import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket 연결 Hook
 * 
 * @param {string} url WebSocket 서버 URL
 * @param {(msg:any)=>void} onMessage 수신 시 호출되는 콜백
 * @param {string|string[]} [protocols] WebSocket 프로토콜
 * @param {number} [reconnectInterval=5000] 재연결 대기시간(ms)
 * @param {number} [maxRetries=3] 최대 재연결 시도 횟수
 * @param {boolean} [debug=false] 디버그 로그 출력 여부
 */
export function useWebSocket(
  url,
  onMessage,
  protocols,
  reconnectInterval = 5000,
  maxRetries = 3,
  debug = false
) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const retryCount = useRef(0);
  const shouldReconnect = useRef(true);

  const [status, setStatus] = useState('connecting');
  const [error, setError] = useState(null);

  const log = (...args) => {
    if (debug) console.log('[WS-Debug]', ...args);
  };

  const connect = useCallback(() => {
    log('connect 호출됨. 재접속 플래그:', shouldReconnect.current);
    if (!shouldReconnect.current) return;

    log('WebSocket 객체 생성 시도:', url);
    const ws = new WebSocket(url, protocols || []);
    wsRef.current = ws;
    setStatus('connecting');
    setError(null);

    ws.onopen = () => {
      log('✅ 연결 성공');
      setStatus('open');
      retryCount.current = 0;
    };

    ws.onmessage = (event) => {
      log('✉️ 메시지 수신');
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        log('⚠️ JSON 파싱 실패, 원본 데이터 전달:', event.data);
        onMessage(event.data);
      }
    };

    ws.onclose = (e) => {
      log('⛔ 연결 종료', e.reason);
      setStatus('closed');
      if (!shouldReconnect.current) return;
      if (retryCount.current < maxRetries) {
        retryCount.current += 1;
        log(`재연결 ${retryCount.current}/${maxRetries} - ${reconnectInterval}ms 후`);
        reconnectTimer.current = setTimeout(connect, reconnectInterval);
      } else {
        log('최대 재시도 횟수 도달. 재접속 중단.');
      }
    };

    ws.onerror = (err) => {
      console.error('❌ WebSocket 에러 발생', err);
      setError(err);
      setStatus('error');
      ws.close();
    };
  }, [url, protocols, reconnectInterval, maxRetries, onMessage]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { socket: wsRef.current, status, error };
}
