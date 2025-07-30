
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from loguru import logger

from server.services.alert_service import AlertService
from server.dependencies import get_alert_service # 새로운 의존성 주입 함수 임포트

router = APIRouter()

@router.websocket("/ws/alerts")
async def websocket_endpoint(
    websocket: WebSocket, 
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    실시간 위험 알림을 위한 WebSocket 엔드포인트입니다.
    클라이언트가 연결되면 ConnectionManager에 등록하고, 연결이 끊어지면 해제합니다.
    """
    manager = alert_service.connection_manager
    await manager.connect(websocket)
    logger.info(f"새로운 클라이언트가 알림 채널에 연결되었습니다: {websocket.client}")
    try:
        while True:
            # 클라이언트로부터 메시지를 받을 수도 있지만, 현재는 서버->클라이언트 단방향 푸시만 사용
            # receive_text()는 연결 유지를 위해 필요합니다.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"클라이언트 연결 종료: {websocket.client}")
