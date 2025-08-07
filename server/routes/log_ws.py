from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from loguru import logger

from server.services.websocket_service import WebSocketService
from server.dependencies import get_websocket_service

router = APIRouter()

@router.websocket("")
async def websocket_log_endpoint(websocket: WebSocket, websocket_service: WebSocketService = Depends(get_websocket_service)):
    """
    실시간 이벤트 로그 스트리밍을 위한 WebSocket 엔드포인트입니다.
    클라이언트가 연결되면 WebSocketService의 로그 채널에 등록됩니다.
    """
    await websocket.accept()

    channel = "logs"
    await websocket_service.connect(websocket, channel)
    try:
        while True:
            # 클라이언트로부터의 메시지는 현재 처리하지 않음
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_service.disconnect(websocket, channel)
