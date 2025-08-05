import os
import platform
import asyncio
from loguru import logger
from typing import List, Dict, Any

from control.serial_communicator import SerialCommunicator
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController, AlertLevel

class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    각 컨트롤러의 인스턴스를 소유하고 관리합니다.
    """
    def __init__(self, mock_mode: bool = False, serial_port: str = None, baud_rate: int = 9600):
        if serial_port is None:
            serial_port = os.environ.get("SERIAL_PORT")
            if not serial_port:
                system = platform.system()
                if system == "Darwin":
                    serial_port = "/dev/cu.usbserial-A5069RR4"
                elif system == "Linux":
                    serial_port = "/dev/ttyUSB0"
                elif system == "Windows":
                    serial_port = "COM1"
                else:
                    raise RuntimeError("Unsupported platform and no serial port specified.")
        
        self.communicator = SerialCommunicator(port=serial_port, baud_rate=baud_rate, mock_mode=mock_mode)
        self.speed_controller = SpeedController(communicator=self.communicator, mock_mode=mock_mode)
        self.power_controller = PowerController(communicator=self.communicator, mock_mode=mock_mode)
        self.alert_controller = AlertController(mock_mode=mock_mode) # AlertController는 동기 방식 유지

        if not self.communicator.mock_mode:
            logger.success("하드웨어 제어 모드가 활성화되었습니다 (모의 모드 OFF).")
        else:
            logger.warning("하드웨어 제어가 비활성화되었습니다 (모의 모드 ON).")

        logger.info("ControlFacade 초기화 완료.")

    async def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        '두뇌(Logic Layer)'가 결정한 액션 목록을 받아 비동기적으로 '근육'을 움직입니다.
        """
        if not actions:
            return

        tasks = []
        for action in actions:
            tasks.append(self._execute_single_action(action))
        
        await asyncio.gather(*tasks)

    async def _execute_single_action(self, action: Dict[str, Any]):
        action_type = action.get("type")
        details = action.get("details", {})
        reason = details.get('reason', '자동 시스템 로직에 의해')

        logger.debug(f"Executing action: {action_type} with reason: {reason}")

        if action_type == "STOP_POWER" or action_type == "PREVENT_POWER_ON" or action_type == "POWER_OFF":
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
                # AlertController는 동기이므로 await 없음
                self.alert_controller.trigger_alert(level=alert_level, message=reason)
            except ValueError:
                logger.error(f"알 수 없는 경고 레벨 문자열: '{level_str}'")
        else:
            logger.warning(f"알 수 없는 제어 액션 타입 '{action_type}'은 무시됩니다.")

    def get_all_statuses(self) -> dict:
        """모든 하위 컨트롤러의 상태를 취합하여 반환합니다. (동기 방식)"""
        power_status = self.power_controller.get_status()
        speed_status = self.speed_controller.get_status()
        alert_status = self.alert_controller.get_system_status()

        statuses = {
            "conveyor_is_on": power_status.get("is_power_on"),
            "conveyor_speed": speed_status.get("current_speed_percent"),
            "is_alert_on": alert_status.get("is_alert_on"),
        }
        return statuses
