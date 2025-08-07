from fastapi import Request, WebSocket, HTTPException
from loguru import logger
from multiprocessing import Queue

from server.services.db_service import DBService
from server.services.websocket_service import WebSocketService
from server.services.zone_service import ZoneService

def get_db_service(request: Request) -> DBService:
    """
    app.state에 저장된 공유 DBService 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'db_service'):
        raise HTTPException(status_code=500, detail="DBService is not initialized.")
    return request.app.state.db_service

def get_websocket_service(websocket: WebSocket) -> WebSocketService:
    """
    app.state에 저장된 공유 WebSocketService 인스턴스를 가져옵니다.
    """
    if not hasattr(websocket.app.state, 'websocket_service'):
        raise HTTPException(status_code=500, detail="WebSocketService is not initialized.")
    return websocket.app.state.websocket_service

def get_zone_service(request: Request) -> ZoneService:
    """
    app.state에 저장된 공유 ZoneService 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'zone_service'):
        raise HTTPException(status_code=500, detail="ZoneService is not initialized.")
    return request.app.state.zone_service

def get_command_queue(request: Request) -> Queue:
    """
    app.state에 저장된 Vision Worker와 통신하기 위한 command_queue를 가져옵니다.
    """
    if not hasattr(request.app.state, 'command_queue'):
        raise HTTPException(status_code=500, detail="Command Queue is not initialized.")
    return request.app.state.command_queue

def get_frame_queue(request: Request) -> Queue:
    """
    app.state에 저장된 Vision Worker로부터 프레임을 수신하는 frame_queue를 가져옵니다.
    """
    if not hasattr(request.app.state, 'frame_queue'):
        raise HTTPException(status_code=500, detail="Frame Queue is not initialized.")
    return request.app.state.frame_queue
