import logging
from typing import List, Dict, Any

from control.alert_controller import AlertController
from control.power_controller import PowerController
from control.speed_controller import SpeedController
# ServiceFacade를 임포트합니다.
from server.service_facade import ServiceFacade

logger = logging.getLogger(__name__)

class ControlFacade:
    def __init__(self, mock_mode: bool = True, service_facade: ServiceFacade = None):
        self.alert_controller = AlertController(mock_mode=mock_mode)
        self.power_controller = PowerController(mock_mode=mock_mode)
        self.speed_controller = SpeedController(mock_mode=mock_mode)
        # ServiceFacade를 주입받습니다.
        self.service_facade = service_facade
        if self.service_facade is None:
            logger.warning("ServiceFacade가 주입되지 않았습니다. 서비스 관련 기능이 제한될 수 있습니다.")
            # 테스트 목적으로 ServiceFacade가 없을 경우를 대비하여 더미 객체 할당
            class DummyServiceFacade:
                def notify_ui(self, *args, **kwargs): pass
                def log_event(self, *args, **kwargs): pass
                def get_system_status(self, *args, **kwargs): return {}
            self.service_facade = DummyServiceFacade()

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        Executes a list of control actions determined by the RuleEngine.
        Each action is a dictionary with 'type' and 'details'.
        """
        for action in actions:
            action_type = action.get("type")
            details = action.get("details", {})

            if action_type == "PREVENT_POWER_ON":
                self.power_controller.prevent_power_on(details.get('reason'))
            elif action_type == "ALLOW_POWER_ON":
                self.power_controller.allow_power_on(details.get('reason'))
            elif action_type == "STOP_POWER":
                self.power_controller.stop_power(details.get('reason'))
            elif action_type == "SLOW_DOWN_50_PERCENT":
                self.speed_controller.slow_down_50_percent(details.get('reason'))
            elif action_type == "TRIGGER_ALARM_CRITICAL":
                self.alert_controller.trigger_critical_alarm(details.get('message'))
            elif action_type == "TRIGGER_ALARM_HIGH":
                self.alert_controller.trigger_high_alarm(details.get('message'))
            elif action_type == "TRIGGER_ALARM_MEDIUM":
                self.alert_controller.trigger_medium_alarm(details.get('message'))
            elif action_type == "NOTIFY_UI":
                self.service_facade.notify_ui(details)
            elif action_type.startswith("LOG_"):
                self.service_facade.log_event(action_type, details)
            else:
                # 알 수 없는 액션 타입은 경고 로그로 남깁니다.
                self.service_facade.logger_service.log_warning(f"Unknown action type: {action_type}")
