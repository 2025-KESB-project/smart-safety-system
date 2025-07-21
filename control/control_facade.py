import logging
from typing import List, Dict, Any

from control.test.alert_controller import AlertController
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.warning_controller import WarningController

# Assuming these services exist for server/DB interaction
# from server.services.alert_service import AlertService
# from server.services.db_service import DBService
# from server.services.logger_service import LoggerService

logger = logging.getLogger(__name__)

class ControlFacade:
    def __init__(self, mock_mode: bool = True):
        self.alert_controller = AlertController(mock_mode=mock_mode)
        self.power_controller = PowerController(mock_mode=mock_mode)
        self.speed_controller = SpeedController(mock_mode=mock_mode)
        self.warning_device = WarningController(mock_mode=mock_mode)
        # self.alert_service = AlertService()
        # self.db_service = DBService()
        # self.logger_service = LoggerService()

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
                self.power_controller.prevent_power_on()
            elif action_type == "ALLOW_POWER_ON":
                self.power_controller.allow_power_on()
            elif action_type == "STOP_POWER":
                self.power_controller.stop_power()
            elif action_type == "SLOW_DOWN_50_PERCENT":
                self.speed_controller.slow_down_50_percent()
            elif action_type == "TRIGGER_ALARM_CRITICAL":
                self.alert_controller.trigger_critical_alarm()
            elif action_type == "TRIGGER_ALARM_HIGH":
                self.alert_controller.trigger_high_alarm()
            elif action_type == "TRIGGER_ALARM_MEDIUM":
                self.alert_controller.trigger_medium_alarm()
            elif action_type == "NOTIFY_UI":
                # This would typically involve sending data to the FastAPI server
                # self.alert_service.send_ui_notification(details)
                logger.info(f"UI Notification: {details.get('message', 'No message')}")
            elif action_type.startswith("LOG_"):
                # This would typically involve logging to DB via db_service or file via logger_service
                # self.db_service.log_event(action_type, details)
                logger.info(f"Logging event: {action_type} - {details}")
            else:
                logger.warning(f"Unknown action type: {action_type}")

# if __name__ == "__main__":
#     # Example Usage
#     logging.basicConfig(level=logging.INFO)
#     facade = ControlFacade()
#
#     # Simulate actions from RuleEngine
#     test_actions_stopped_critical = [
#         {"type": "PREVENT_POWER_ON", "details": {"reason": "Person in danger zone"}},
#         {"type": "TRIGGER_ALARM_CRITICAL", "details": {"level": "critical"}},
#         {"type": "LOG_LOTO_ACTIVE", "details": {"timestamp": "...", "zone": "..."}},
#         {"type": "NOTIFY_UI", "details": {"message": "LOTO Active: Person detected in danger zone!"}}
#     ]
#
#     test_actions_operating_high = [
#         {"type": "SLOW_DOWN_50_PERCENT", "details": {"reason": "Person detected"}},
#         {"type": "TRIGGER_ALARM_HIGH", "details": {"level": "high"}},
#         {"type": "LOG_HIGH_RISK", "details": {"timestamp": "...", "zone": "..."}},
#         {"type": "NOTIFY_UI", "details": {"message": "Conveyor slowed: Person detected near belt!"}}
#     ]
#
#     test_actions_operating_safe = [
#         {"type": "LOG_NORMAL_OPERATION", "details": {"timestamp": "..."}},
#         {"type": "NOTIFY_UI", "details": {"message": "System operating normally."}}
#     ]
#
#     logger.info("\n--- Executing Stopped Critical Actions ---")
#     facade.execute_actions(test_actions_stopped_critical)
#
#     logger.info("\n--- Executing Operating High Actions ---")
#     facade.execute_actions(test_actions_operating_high)
#
#     logger.info("\n--- Executing Operating Safe Actions ---")
#     facade.execute_actions(test_actions_operating_safe)
