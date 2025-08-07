from loguru import logger
import time
from typing import Dict, List, Tuple
from enum import Enum
import threading

from core.serial_communicator import SerialCommunicator


class AlertLevel(Enum):
    """경고 수준"""
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertDevice(Enum):
    """경고 장치 종류"""
    PIEZO_BUZZER = "piezo_buzzer"


class AlertController:
    """피에조 부저 경고 제어 시스템"""

    def __init__(self, communicator: SerialCommunicator = None, mock_mode: bool = True):
        """
        경고 제어기를 초기화합니다.
        :param communicator: 시리얼 통신 객체
        :param mock_mode: 모의 모드 여부
        """
        self.mock_mode = mock_mode
        self.communicator = communicator

        self.device_status: Dict[str, str] = {AlertDevice.PIEZO_BUZZER.value: "idle"}
        self.is_alerting: Dict[AlertLevel, bool] = {level: False for level in AlertLevel}  # 경고 상태 플래그
        self._lock = threading.Lock()

        # 위험 수준별 부저 경고음 명령어 맵
        self.buzzer_commands = {
            AlertLevel.MEDIUM: "b_medium",
            AlertLevel.HIGH: "b_high",
            AlertLevel.CRITICAL: "b_critical"
        }

        # 경고 지속 시간 (파이썬 레벨에서 중복 경고를 방지하기 위함)
        self.alert_duration = 3  # 초

        if not self.mock_mode and self.communicator is None:
            raise ValueError("실제 모드에서는 communicator 객체가 반드시 필요합니다.")
        logger.info(f"피에조 부저 경고 제어기 초기화: 모의 모드: {self.mock_mode}")

    def trigger_alert(self, level: AlertLevel, message: str = ""):
        """
        지정된 위험 수준에 따라 피에조 부저 경고를 발생시킵니다.
        이미 해당 경고가 울리고 있으면 아무것도 하지 않습니다.
        """
        if not isinstance(level, AlertLevel):
            logger.error(f"잘못된 경고 수준: {level}")
            return

        with self._lock:
            if self.is_alerting[level]:
                # logger.debug(f"[{level.value.upper()}] 경고가 이미 활성화 상태입니다.")
                return  # 이미 경고 중이면 중복 실행 방지

            # 경고 시작
            self.is_alerting[level] = True
            logger.info(f"[{level.value.upper()}] 경고 발생. 장치: {AlertDevice.PIEZO_BUZZER.value}")

            # 피에조 부저 명령 전송
            if not self.mock_mode:
                command = self.buzzer_commands.get(level)
                if command:
                    self.communicator.send_command(command)
                    logger.info(f"피에조 부저 명령 전송: {command}")

            self._activate_device_internal()

    def stop_alert(self, level: AlertLevel):
        """
        지정된 레벨의 경고를 중지합니다.
        """
        if not isinstance(level, AlertLevel):
            logger.error(f"잘못된 경고 수준: {level}")
            return

        with self._lock:
            if not self.is_alerting[level]:
                return  # 경고가 울리고 있지 않으면 아무것도 하지 않음

            logger.info(f"[{level.value.upper()}] 경고 중지.")
            self.is_alerting[level] = False
            self._deactivate_alert_internal()

            if not self.mock_mode:
                # 아두이노에 부저 정지 명령 전송 (예: b_stop)
                self.communicator.send_command("b_stop")
                logger.info("피에조 부저 정지 명령 전송: b_stop")

    def _activate_device_internal(self):
        """(내부용) 부저 장치를 활성화 상태로 변경합니다."""
        self.device_status[AlertDevice.PIEZO_BUZZER.value] = "active"

    def _deactivate_alert_internal(self):
        """(내부용) 특정 레벨의 경고를 비활성화합니다."""
        with self._lock:
            self.device_status[AlertDevice.PIEZO_BUZZER.value] = "idle"

    def trigger_medium_alarm(self, message: str = "Medium risk detected"):
        self.trigger_alert(AlertLevel.MEDIUM, message)

    def trigger_high_alarm(self, message: str = "High risk detected"):
        self.trigger_alert(AlertLevel.HIGH, message)

    def trigger_critical_alarm(self, message: str = "Critical risk detected"):
        self.trigger_alert(AlertLevel.CRITICAL, message)

    def get_status(self) -> Dict[str, bool]:
        """다른 컨트롤러와 일관성을 맞춘 상태 반환 메소드."""
        # 현재 어떤 레벨의 경고라도 활성화되어 있는지 확인
        is_alerting = any(self.is_alerting.values())
        return {"is_alert_on": is_alerting}

    def get_all_statuses(self) -> Dict[str, str]:
        """모든 장치의 상태를 반환합니다."""
        return self.device_status

    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'mock_mode': self.mock_mode,
            'device_statuses': self.get_all_statuses()
        }