import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket 연결을 관리하고, 메시지를 수신하면 onMessage 콜백을 호출합니다.
 * 
 * @param {string} url WebSocket 서버 URL
 * @param {(msg: any) => void} onMessage 수신한 메시지를 처리할 콜백
 * @param {string|string[]} [protocols] 프로토콜 (선택)
 * @param {number} [reconnectInterval=5000] 재접속 시도 간격 (ms)
 * @param {number} [maxRetries=3] 최대 재접속 시도 횟수
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
    if (debug) console.log(...args);
  };

  const connect = useCallback(() => {
    log("[WS] connect 호출됨. 재접속 플래그:", shouldReconnect.current);
    if (!shouldReconnect.current) return;

    log("[WS] WebSocket 객체 생성 시도:", url);
    const ws = new WebSocket(url, protocols || []);
    wsRef.current = ws;
    setStatus('connecting');
    setError(null);

    ws.onopen = () => {
      log("[WS] ✅ 연결 성공 (onopen)");
      setStatus('open');
      retryCount.current = 0;
    };

    ws.onmessage = (event) => {
      log("[WS] ✉️ 메시지 수신");
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {
        onMessage(event.data);
      }
    };

    ws.onclose = (e) => {
      log("[WS] ⛔️ 연결 종료 (onclose)");
      setStatus('closed');
      if (!shouldReconnect.current) return;
      if (retryCount.current < maxRetries) {
        retryCount.current += 1;
        console.warn(
          `[WS] 연결 끊김 (reason: ${e.reason}), ${reconnectInterval}ms 후 재시도 (${retryCount.current}/${maxRetries})`
        );
        reconnectTimer.current = setTimeout(connect, reconnectInterval);
      } else {
        console.error(`[WS] 최대 재시도 횟수(${maxRetries}) 도달. 재접속 중단`);
      }
    };

    ws.onerror = (err) => {
      console.error("[WS] ❌ 에러 발생", err);
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
