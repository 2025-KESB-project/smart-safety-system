import logging
from typing import List, Dict, Any

from control.alert_controller import AlertController
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from server.services.alert_service import AlertService
from server.services.db_service import DBService
from server.services.logger_service import LoggerService

logger = logging.getLogger(__name__)

class ControlFacade:
    def __init__(self, mock_mode: bool = True):
        self.alert_controller = AlertController(mock_mode=mock_mode)
        self.power_controller = PowerController(mock_mode=mock_mode)
        self.speed_controller = SpeedController(mock_mode=mock_mode)
        self.alert_service = AlertService()
        self.db_service = DBService()
        self.logger_service = LoggerService()

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        Executes a list of control actions determined by the RuleEngine.
        Each action is a dictionary with 'type' and 'details'.
        """
        for action in actions:
            action_type = action.get("type")
            details = action.get("details", {})
            
            logger.info(f"Executing action: {action_type} with details: {details}")

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
                self.alert_service.send_ui_notification(details)
            elif action_type.startswith("LOG_"):
                self.db_service.log_event(action_type, details)
                self.logger_service.log_info(f"Event: {action_type} - {details}")
            else:
                self.logger_service.log_warning(f"Unknown action type: {action_type}")