from loguru import logger
from typing import List, Dict, Any, Optional

from core.serial_communicator import SerialCommunicator
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController, AlertLevel

class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    SerialCommunicator를 외부에서 주입받아 사용합니다.
    """
    def __init__(self, communicator: Optional[SerialCommunicator] = None, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.communicator = communicator

        if not self.mock_mode and self.communicator is None:
            raise ValueError("ControlFacade requires a SerialCommunicator in non-mock mode.")

        # 주입된 communicator를 각 컨트롤러에 전달합니다.
        self.speed_controller = SpeedController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.power_controller = PowerController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.alert_controller = AlertController(communicator=self.communicator, mock_mode=self.mock_mode)

        if not self.mock_mode:
            logger.success("하드웨어 제어 모드가 활성화되었습니다 (모의 모드 OFF).")
        else:
            logger.warning("하드웨어 제어가 비활성화되었습니다 (모의 모드 ON).")

        logger.info("ControlFacade 초기화 완료.")

    def get_communicator(self) -> SerialCommunicator:
        """소유하고 있는 SerialCommunicator의 참조를 반환합니다."""
        return self.communicator

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

            # action_type이 문자열이 아닌 경우(None 등)를 건너뛰는 안전장치
            if not isinstance(action_type, str):
                logger.warning(f"잘못되었거나 누락된 액션 타입: {action}")
                continue

            logger.debug(f"Executing action: {action_type} with reason: {reason}")

            # Action 타입을 보고 적절한 컨트롤러의 메소드를 호출합니다.
            if action_type == "STOP_POWER" or action_type == "PREVENT_POWER_ON" or action_type == "POWER_OFF":
                # 2중 안전 장치: 릴레이 전원과 모터 속도를 모두 차단합니다.
                self.power_controller.power_off(reason)
                self.speed_controller.stop_conveyor(reason)
            elif action_type == "POWER_ON": # API 등 외부 요청을 위한 액션
                self.power_controller.power_on(reason)
            elif action_type == "REDUCE_SPEED_50":
                self.speed_controller.slow_down_50_percent(reason)
            elif action_type == "RESUME_FULL_SPEED":
                self.speed_controller.resume_full_speed(reason)
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
        power_status = self.power_controller.get_status()
        speed_status = self.speed_controller.get_status()
        alert_status = self.alert_controller.get_system_status()

        # API 응답 모델(SystemStatusResponse)에 맞게 키 이름을 통일합니다.
        statuses = {
            "conveyor_is_on": power_status.get("is_power_on"),
            "conveyor_speed": speed_status.get("current_speed_percent"),
            "is_alert_on": alert_status.get("is_alert_on"),
        }
        return statuses

    def release(self):
        """ControlFacade와 모든 하위 컨트롤러의 리소스를 해제합니다."""
        logger.info("ControlFacade 리소스를 해제합니다...")
        self.communicator.close() # SerialCommunicator의 연결을 닫습니다.
        logger.info("ControlFacade 리소스 해제 완료.")