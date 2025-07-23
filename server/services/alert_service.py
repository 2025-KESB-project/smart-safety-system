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
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"새로운 클라이언트 연결: {websocket.client}. 총 {len(self.active_connections)}명 접속 중.")

    def disconnect(self, websocket: Any): # websocket: WebSocket
        """클라이언트 연결을 종료합니다."""
        self.active_connections.remove(websocket)
        logger.info(f"클라이언트 연결 해제: {websocket.client}. 총 {len(self.active_connections)}명 접속 중.")

    async def broadcast(self, message: Dict[str, Any]):
        """연결된 모든 클라이언트에게 메시지를 브로드캐스트합니다."""
        for connection in self.active_connections:
            await connection.send_json(message)

class AlertService:
    """UI 클라이언트에게 WebSocket을 통해 실시간 알림을 보내는 서비스"""

    def __init__(self, config: Dict = None):
        """
        AlertService를 초기화합니다.
        """
        self.config = config or {}
        self.connection_manager = ConnectionManager()
        logger.info("AlertService 초기화 완료. (WebSocket 준비)")

    def send_ui_notification(self, details: Dict[str, Any]):
        """
        연결된 모든 UI 클라이언트에게 알림을 보냅니다.
        실제 애플리케이션에서는 비동기적으로 처리되어야 합니다.
        """
        logger.info(f"UI 알림 전송 준비: {details}")
        # asyncio.create_task(self.connection_manager.broadcast(details))
        # 현재는 동기 환경이므로 위 코드는 주석 처리합니다.
        # FastAPI 앱 내에서 실행될 때 실제 broadcast를 호출하게 됩니다.
        pass

    def get_status(self) -> Dict[str, Any]:
        """서비스의 현재 상태를 반환합니다."""
        return {
            "connected_clients": len(self.connection_manager.active_connections)
        }