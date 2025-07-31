from loguru import logger
from typing import List, Dict, Any

# 변경된 PowerController를 임포트합니다.
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController
from server.services.websocket_service import WebSocketService
from server.services.db_service import DBService

class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    각 컨트롤러의 인스턴스를 소유하고 관리합니다.
    """
    def __init__(self, mock_mode: bool = True, alert_service: WebSocketService = None, db_service: DBService = None):
        # 각 컨트롤러의 인스턴스를 생성하여 소유합니다.
        self.power_controller = PowerController(mock_mode=mock_mode)
        self.speed_controller = SpeedController(mock_mode=mock_mode)
        self.alert_controller = AlertController(mock_mode=mock_mode)
        
        # 외부 서비스(UI 알림, DB 로깅)를 위한 서비스 객체를 주입받습니다.
        self.alert_service = alert_service
        self.db_service = db_service
        logger.info("ControlFacade 초기화 완료.")

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        '두뇌(Logic Layer)'가 결정한 액션 목록을 받아 '근육'을 움직입니다.
        """
        if not actions:
            return

        # 나중에 우선순위가 필요할 경우를 대비해 정렬할 수 있습니다.
        # actions.sort(key=lambda x: x.get('priority', 100))

        for action in actions:
            action_type = action.get("type")
            details = action.get("details", {})
            reason = details.get('reason', '자동 시스템 로직에 의해')

            logger.debug(f"Executing action: {action_type} with reason: {reason}")

            if action_type == "POWER_ON":
                self.power_controller.turn_on(reason)
            elif action_type == "POWER_OFF":
                self.power_controller.turn_off(reason)
            elif action_type == "REDUCE_SPEED_50":
                self.speed_controller.slow_down_50_percent(reason)
            elif action_type == "TRIGGER_ALARM":
                level = details.get('level', 'medium')
                message = details.get('message', '알 수 없는 경고')
                self.alert_controller.trigger_alarm(level, message)
            elif action_type == "NOTIFY_UI":
                if self.alert_service:
                    # 비동기 함수를 호출해야 할 경우, 이벤트 루프를 통해 실행해야 합니다.
                    # 여기서는 단순화를 위해 직접 호출 가능한 동기 함수라고 가정합니다.
                    # 실제 구현에서는 asyncio.run_coroutine_threadsafe 등을 사용해야 합니다.
                    logger.info(f"UI 알림: {details}")
                else:
                    logger.warning("AlertService가 없어 UI 알림을 보낼 수 없습니다.")
            elif action_type.startswith("LOG_"):
                if self.db_service:
                    log_data = {
                        "event_type": action_type,
                        "details": details,
                        "risk_level": details.get("risk_level", "N/A")
                    }
                    self.db_service.log_event(log_data)
                else:
                    logger.warning("DBService가 없어 이벤트를 기록할 수 없습니다.")
            else:
                logger.warning(f"알 수 없는 액션 타입 '{action_type}'은 무시됩니다.")

    def get_power_status(self) -> dict:
        """PowerController의 현재 상태를 조회하여 반환합니다."""
        return self.power_controller.get_status()