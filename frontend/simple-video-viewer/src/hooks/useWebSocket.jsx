// src/hooks/useWebSocket.js
import { useEffect, useRef } from 'react';

/**
 * WebSocket 연결을 관리하고, 메시지를 수신하면 onMessage 콜백을 호출합니다.
 *
 * @param {string} url WebSocket 서버 URL (ws:// 또는 wss://)
 * @param {(msg: any) => void} onMessage 수신한 메시지를 처리할 콜백
 * @param {string|string[]} [protocols] 프로토콜 (선택)
 * @param {number} [reconnectInterval=3000] 재접속 시도 간격 (ms)
 */
export function useWebSocket(
  url,
  onMessage,
  protocols,
  reconnectInterval = 3000
) {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(url, protocols || []);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to', url);
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
        console.warn(
          '[WS] Disconnected, retrying in',
          reconnectInterval,
          'ms',
          e.reason
        );
        reconnectTimerRef.current = window.setTimeout(connect, reconnectInterval);
      };

      ws.onerror = (err) => {
        console.error('[WS] Error', err);
        ws.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url, protocols, reconnectInterval, onMessage]);

  return wsRef.current;
}
