import os
import platform

from loguru import logger
from typing import List, Dict, Any

from control.serial_communicator import SerialCommunicator
from control.alert_controller import AlertController
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
    def __init__(self, mock_mode: bool = False, serial_port: str = None, baud_rate: int = 9600):
        # Determine serial port if not provided
        if serial_port is None:
            serial_port = os.environ.get("SERIAL_PORT")
            if not serial_port:
                system = platform.system()
                if system == "Darwin":  # macOS
                    serial_port = "/dev/cu.usbserial-A5069RR4"
                elif system == "Linux":
                    serial_port = "/dev/ttyUSB0"
                elif system == "Windows":
                    serial_port = "COM1"
                else:
                    raise RuntimeError("Unsupported platform and no serial port specified.")
        # 1. 시리얼 통신을 전담할 단일 인스턴스를 생성합니다.
        self.communicator = SerialCommunicator(port=serial_port, baud_rate=baud_rate, mock_mode=mock_mode)
        # 2. 생성된 communicator를 각 컨트롤러에 주입합니다.
        self.speed_controller = SpeedController(communicator=self.communicator, mock_mode=mock_mode)
        self.power_controller = PowerController(communicator=self.communicator, mock_mode=mock_mode)
        self.alert_controller = AlertController(mock_mode=mock_mode)

        # 최종 하드웨어 연결 상태를 요약하여 로깅합니다.
        if not self.communicator.mock_mode:
            logger.success("하드웨어 제어 모드가 활성화되었습니다 (모의 모드 OFF).")
        else:
            logger.warning("하드웨어 제어가 비활성화되었습니다 (모의 모드 ON).")

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