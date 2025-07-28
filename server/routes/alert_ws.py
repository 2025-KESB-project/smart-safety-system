
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from loguru import logger

from server.service_facade import ServiceFacade
from server.dependencies import get_service_facade # 의존성 주입 함수 임포트

router = APIRouter()

@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket, sf: ServiceFacade = Depends(get_service_facade)):
    """
    실시간 위험 알림을 위한 WebSocket 엔드포인트입니다.
    클라이언트가 연결되면 ConnectionManager에 등록하고, 연결이 끊어지면 해제합니다.
    """
    manager = sf.alert_service.connection_manager
    await manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지를 받을 수도 있지만, 현재는 서버->클라이언트 단방향 푸시만 사용
            data = await websocket.receive_text()
            logger.debug(f"클라이언트로부터 메시지 수신: {data}") # 디버깅용
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"클라이언트 연결 종료: {websocket.client}")
