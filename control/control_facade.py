import os
import platform
from loguru import logger
from typing import List, Dict, Any

from control.serial_communicator import SerialCommunicator
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController, AlertLevel


class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    모든 제어 로직은 동기(Synchronous) 방식으로 작동합니다.
    """
    def __init__(self, mock_mode: bool = False, serial_port: str = None, baud_rate: int = 9600):
        self.mock_mode = mock_mode

        # 시리얼 포트가 명시되지 않고, 모의 모드가 아닐 경우 자동 탐지
        if not self.mock_mode and serial_port is None:
            serial_port = self._find_serial_port()

        # 자동 탐지 실패 시 모의 모드로 강제 전환
        if not self.mock_mode and not serial_port:
            logger.critical("시리얼 포트를 찾을 수 없어 모의 모드로 강제 전환합니다. 하드웨어 제어가 비활성화됩니다.")
            self.mock_mode = True

        # 컨트롤러 초기화 및 의존성 주입
        self.communicator = SerialCommunicator(port=serial_port, baud_rate=baud_rate, mock_mode=self.mock_mode)
        self.power_controller = PowerController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.speed_controller = SpeedController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.alert_controller = AlertController(mock_mode=self.mock_mode)

        if not self.mock_mode:
            logger.success("하드웨어 제어 모드가 활성화되었습니다 (모의 모드 OFF).")
        else:
            logger.warning("하드웨어 제어가 비활성화되었습니다 (모의 모드 ON).")
        logger.info("ControlFacade 초기화 완료.")

    def _find_serial_port(self) -> str | None:
        """환경 변수 또는 OS를 기반으로 시리얼 포트를 탐지합니다."""
        port = os.environ.get("SERIAL_PORT")
        if port:
            logger.info(f"환경 변수에서 시리얼 포트 발견: {port}")
            return port

        system = platform.system()
        if system == "Darwin":
            return "/dev/cu.usbserial-A5069RR4"
        elif system == "Linux":
            return "/dev/ttyUSB0"
        elif system == "Windows":
            return "COM1"
        
        logger.warning(f"지원되지 않는 OS '{system}' 또는 연결된 시리얼 장치 없음.")
        return None

    async def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        '두뇌(Logic Layer)'가 결정한 액션 목록을 받아 비동기적으로 실행합니다.
        """
        if not actions:
            return

        for action in actions:
            action_type = action.get("type")
            reason = action.get("details", {}).get('reason', '자동 시스템 로직')

            if not isinstance(action_type, str):
                logger.warning(f"잘못된 액션 타입: {action}")
                continue

            logger.debug(f"실행할 액션: {action_type}, 이유: {reason}")

            if action_type in ("STOP_POWER", "PREVENT_POWER_ON", "POWER_OFF"):
                await self.power_controller.power_off(reason)
                await self.speed_controller.stop_conveyor(reason)
            elif action_type == "POWER_ON":
                await self.power_controller.power_on(reason)
            elif action_type == "REDUCE_SPEED_50":
                await self.speed_controller.slow_down_50_percent(reason)
            elif action_type == "RESUME_FULL_SPEED":
                await self.speed_controller.resume_full_speed(reason)
            elif action_type.startswith("TRIGGER_ALARM_"):
                level_str = action_type.replace("TRIGGER_ALARM_", "").lower()
                try:
                    alert_level = AlertLevel(level_str)
                    self.alert_controller.trigger_alert(level=alert_level, message=reason)
                except ValueError:
                    logger.error(f"알 수 없는 경고 레벨: '{level_str}'")
            else:
                logger.warning(f"알 수 없는 제어 액션 '{action_type}'은 무시됩니다.")

    async def get_all_statuses(self) -> dict:
        """모든 하위 컨트롤러의 상태를 비동기적으로 취합하여 반환합니다."""
        power_status = await self.power_controller.get_status()
        speed_status = await self.speed_controller.get_status()
        alert_status = await self.alert_controller.get_status()

        return {
            "conveyor_is_on": power_status.get("is_power_on"),
            "conveyor_speed": speed_status.get("current_speed_percent"),
            "is_alert_on": alert_status.get("is_alert_on"),
        }

    def release(self):
        """ControlFacade와 모든 하위 컨트롤러의 리소스를 해제합니다."""
        logger.info("ControlFacade 리소스를 해제합니다...")
        self.communicator.close()
        logger.info("ControlFacade 리소스 해제 완료.")
