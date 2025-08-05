from fastapi import Request, WebSocket
from loguru import logger

# 아키텍처 변경으로 인한 임포트 경로 수정
from server.state_manager import SystemStateManager
from control.control_facade import ControlFacade
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from server.services.db_service import DBService
from server.services.websocket_service import WebSocketService
from server.services.zone_service import ZoneService

# --- 중앙 관리 객체 의존성 ---

def get_state_manager(request: Request) -> SystemStateManager:
    """
    app.state에 저장된 공유 SystemStateManager 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'state_manager'):
        logger.critical("SystemStateManager가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("SystemStateManager is not initialized.")
    return request.app.state.state_manager

def get_control_facade(request: Request) -> ControlFacade:
    """
    app.state에 저장된 공유 ControlFacade 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'control_facade'):
        logger.critical("ControlFacade가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("ControlFacade is not initialized.")
    return request.app.state.control_facade

def get_detector(request: Request) -> Detector:
    """
    app.state에 저장된 공유 Detector 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'detector'):
        logger.critical("Detector가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("Detector is not initialized.")
    return request.app.state.detector

def get_logic_facade(request: Request) -> LogicFacade:
    """
    app.state에 저장된 공유 LogicFacade 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'logic_facade'):
        logger.critical("LogicFacade가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("LogicFacade is not initialized.")
    return request.app.state.logic_facade

def get_db_service(request: Request) -> DBService:
    """
    app.state에 저장된 공유 DBService 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'db_service'):
        logger.critical("DBService가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("DBService is not initialized.")
    return request.app.state.db_service

def get_websocket_service(websocket: WebSocket) -> 'WebSocketService':
    """
    app.state에 저장된 공유 WebSocketService 인스턴스를 가져옵니다.
    """
    if not hasattr(websocket.app.state, 'websocket_service'):
        logger.critical("WebSocketService가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("WebSocketService is not initialized.")
    return websocket.app.state.websocket_service

def get_zone_service(request: Request) -> ZoneService:
    """
    app.state에 저장된 공유 ZoneService 인스턴스를 가져옵니다.
    """
    if not hasattr(request.app.state, 'zone_service'):
        logger.critical("ZoneService가 app.state에 초기화되지 않았습니다!")
        raise RuntimeError("ZoneService is not initialized.")
    return request.app.state.zone_service