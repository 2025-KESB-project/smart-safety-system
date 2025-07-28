from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from loguru import logger

from server.services.db_service import DBService
from server.dependencies import get_db_service

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_log_endpoint(websocket: WebSocket, db_service: DBService = Depends(get_db_service)):
    """
    실시간 이벤트 로그 스트리밍을 위한 WebSocket 엔드포인트입니다.
    클라이언트가 연결되면 DBService의 로그 연결 관리자에 등록됩니다.
    """
    if not hasattr(db_service, 'log_connection_manager'):
        logger.error("DBService에 log_connection_manager가 설정되지 않았습니다.")
        await websocket.close(code=1011, reason="Server configuration error")
        return

    manager = db_service.log_connection_manager
    await manager.connect(websocket)
    logger.info(f"로그 스트림 클라이언트 연결: {websocket.client}")
    try:
        while True:
            # 클라이언트로부터의 메시지는 현재 처리하지 않음
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"로그 스트림 클라이언트 연결 종료: {websocket.client}")
