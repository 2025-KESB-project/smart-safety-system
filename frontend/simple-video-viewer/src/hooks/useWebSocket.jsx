// src/hooks/useWebSocket.js
import { useEffect, useRef } from 'react';

/**
 * WebSocket 연결을 관리하고, 메시지를 수신하면 onMessage 콜백을 호출합니다.
 *
 * @param {string} url WebSocket 서버 URL (ws:// 또는 wss://)
 * @param {(msg: any) => void} onMessage 수신한 메시지를 처리할 콜백
 * @param {string|string[]} [protocols] 프로토콜 (선택)
 * @param {number} [reconnectInterval=3000] 재접속 시도 간격 (ms)
 * @param {number} [maxRetries=3] 최대 재접속 시도 횟수
 */
export function useWebSocket(
  url,
  onMessage,
  protocols,
  reconnectInterval = 5000,
  maxRetries = 3
  //5초당 재접속 시도, 최대 3회
) {
  const wsRef          = useRef(null);
  const reconnectTimer = useRef(null);
  const retryCount     = useRef(0);  // 재접속 시도 횟수를 추적하는 변수
  const shouldReconnect = useRef(true); // 재접속 여부를 제어하는 플래그
  //상태-에러 관리용 state
  const [status, setStatus] = useState('connecting'); // 연결 상태를 추적하는 상태 변수
  const [error, setError] = useState(null); // 오류 상태를 추적하는 상태 변수

  useEffect(() => {
    shouldReconnect.current = true; // 컴포넌트가 마운트될 시 활성화

    function connect() {
      if (!shouldReconnect.current) return; // 재접속이 비활성화된 경우 연결하지 않음
      const ws = new WebSocket(url, protocols || []);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to', url);
        // 연결 성공 시 재시도 카운트 초기화
        retryCount.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch {
          onMessage(event.data);
        }
      };

      ws.onclose = (e) => {
        if (!shouldReconnect.current) return; // 재접속이 비활성화된 경우 연결 종료
        if (retryCount.current < maxRetries) {
          retryCount.current += 1;
          console.warn(
            `[WS] Disconnected (reason: ${e.reason}), retry ${retryCount.current}/${maxRetries} in ${reconnectInterval}ms`
          );
          reconnectTimer.current = setTimeout(connect, reconnectInterval);
        } else {
          console.error(
            `[WS] Disconnected. Max retries (${maxRetries}) reached. No further reconnects.`
          );
        }
      };// 연결이 닫힐 때마다 재접속 시도, 최대 재접속 횟수 초과 시 중단

      ws.onerror = (err) => {
        console.error('[WS] Error', err);
        // 오류 발생 시 연결 닫기 → onclose 로직 수행
        ws.close();
      };
    }

    connect();

    return () => {
      shouldReconnect.current = false; // 컴포넌트 언마운트 시 재접속 비활성화
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [url, protocols, reconnectInterval, maxRetries, onMessage]);

  return { socket: wsRef.current, status, error };
}
