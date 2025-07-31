from loguru import logger
from typing import List, Dict, Any

# 변경된 PowerController를 임포트합니다.
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController, AlertLevel # AlertLevel 임포트
from server.services.websocket_service import WebSocketService
from server.services.db_service import DBService

class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    각 컨트롤러의 인스턴스를 소유하고 관리합니다.
    """
    def __init__(self, mock_mode: bool = True):
        # 각 컨트롤러의 인스턴스를 생성하여 소유합니다.
        self.power_controller = PowerController(mock_mode=mock_mode)
        self.speed_controller = SpeedController(mock_mode=mock_mode)
        self.alert_controller = AlertController(mock_mode=mock_mode)
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
            elif action_type.startswith("TRIGGER_ALARM_"):
                # "TRIGGER_ALARM_CRITICAL" -> "critical"
                level_str = action_type.replace("TRIGGER_ALARM_", "").lower()
                try:
                    # 문자열을 AlertLevel Enum 멤버로 변환
                    alert_level = AlertLevel(level_str)
                    self.alert_controller.trigger_alert(level=alert_level, message=reason)
                except ValueError:
                    logger.error(f"알 수 없는 경고 레벨 문자열: '{level_str}'")
            else:
                logger.warning(f"알 수 없는 제어 액션 타입 '{action_type}'은 무시됩니다.")

    def get_power_status(self) -> dict:
        """PowerController의 현재 상태를 조회하여 반환합니다."""
        return self.power_controller.get_status()

    def get_all_statuses(self) -> dict:
        """모든 하위 컨트롤러의 상태를 취합하여 반환합니다."""
        statuses = {}
        statuses.update(self.power_controller.get_status())
        statuses.update(self.speed_controller.get_status())
        statuses.update(self.alert_controller.get_system_status())
        return statuses