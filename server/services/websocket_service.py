from typing import Dict, Any, List
import asyncio
from loguru import logger

# FastAPI의 WebSocket을 사용하기 위한 임포트 (실제 앱에서는 주석 해제)
# from fastapi import WebSocket

class ConnectionManager:
    """WebSocket 연결을 관리하는 중앙 관리자 클래스"""
    def __init__(self):
        self.active_connections: List[Any] = [] # 실제로는 List[WebSocket] 타입

    async def connect(self, websocket: Any): # websocket: WebSocket
        """새로운 클라이언트 연결을 수락합니다."""
        self.active_connections.append(websocket)
        logger.info(f"Client added: {websocket.client}. Total: {len(self.active_connections)}.")

    def disconnect(self, websocket: Any): # websocket: WebSocket
        """클라이언트 연결을 종료합니다."""
        try:
            self.active_connections.remove(websocket)
            logger.info(f"Client removed: {websocket.client}. Total: {len(self.active_connections)}.")
        except ValueError:
            logger.warning(f"Attempted to remove a client that was not in the list: {websocket.client}")

    async def broadcast(self, message: Dict[str, Any]):
        """연결된 모든 클라이언트에게 메시지를 브로드캐스트합니다."""
        # 메시지 타입이나 주요 정보를 로그에 남겨서 디버깅을 용이하게 합니다.
        msg_type_for_log = message.get('type') or message.get('data', {}).get('event_type', 'Unknown')
        logger.info(f"Broadcasting message (type: {msg_type_for_log}) to {len(self.active_connections)} client(s).")

        # 클라이언트가 닫힌 연결에 메시지를 보내려고 할 때 발생하는 오류를 방지합니다.
        active_connections = self.active_connections[:] # 반복 중 리스트 변경을 피하기 위해 복사본 사용
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"클라이언트로 메시지 전송 실패: {e}. 해당 연결을 제거합니다.")
                self.disconnect(connection)

class WebSocketService:
    """모든 WebSocket 채널(logs, alerts 등)을 중앙에서 관리하는 서비스"""

    def __init__(self):
        """WebSocketService를 초기화하고, 채널별로 ConnectionManager를 생성합니다."""
        self.managers: Dict[str, ConnectionManager] = {
            "logs": ConnectionManager(),
            "alerts": ConnectionManager()
        }
        logger.info(f"WebSocketService 초기화 완료. 관리 채널: {list(self.managers.keys())}")

    async def connect(self, websocket: Any, channel: str):
        """특정 채널에 클라이언트를 연결합니다."""
        manager = self.managers.get(channel)
        if manager:
            await manager.connect(websocket)
            logger.info(f"클라이언트가 '{channel}' 채널에 연결되었습니다.")
        else:
            logger.error(f"'{channel}' 채널을 찾을 수 없어 연결에 실패했습니다.")

    def disconnect(self, websocket: Any, channel: str):
        """특정 채널에서 클라이언트 연결을 종료합니다."""
        manager = self.managers.get(channel)
        if manager:
            manager.disconnect(websocket)
            logger.info(f"클라이언트가 '{channel}' 채널에서 연결 해제되었습니다.")

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """특정 채널의 모든 클라이언트에게 메시지를 브로드캐스트합니다."""
        manager = self.managers.get(channel)
        if manager:
            await manager.broadcast(message)
        else:
            logger.warning(f"'{channel}' 채널을 찾을 수 없어 브로드캐스트에 실패했습니다.")

    def get_status(self) -> Dict[str, Any]:
        """서비스의 현재 상태 (채널별 접속자 수)를 반환합니다."""
        return {
            channel: len(manager.active_connections)
            for channel, manager in self.managers.items()
        }