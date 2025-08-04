from loguru import logger
import time
from typing import Dict, List, Tuple
from enum import Enum
import threading

from control.serial_communicator import SerialCommunicator

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
        self.is_alerting: Dict[AlertLevel, bool] = {level: False for level in AlertLevel} # 경고 상태 플래그
        self._lock = threading.Lock()

        # 위험 수준별 부저 경고음 명령어 맵
        self.buzzer_commands = {
            AlertLevel.MEDIUM: "b_medium",
            AlertLevel.HIGH: "b_high",
            AlertLevel.CRITICAL: "b_critical"
        }
        
        # 경고 지속 시간 (파이썬 레벨에서 중복 경고를 방지하기 위함)
        self.alert_duration = 3 # 초

        if not self.mock_mode and self.communicator is None:
            raise ValueError("실제 모드에서는 communicator 객체가 반드시 필요합니다.")
        logger.info(f"피에조 부저 경고 제어기 초기화: 모의 모드: {self.mock_mode}")

    def trigger_alert(self, level: AlertLevel, message: str = ""):
        """
        지정된 위험 수준에 따라 피에조 부저 경고를 발생시킵니다.
        한 번 발생한 경고는 지정된 시간이 지날 때까지 다시 발생하지 않습니다.
        """
        if not isinstance(level, AlertLevel):
            logger.error(f"잘못된 경고 수준: {level}")
            return

        with self._lock:
            if self.is_alerting[level]:
                return # 이미 경고 중이면 중복 실행 방지

            # 경고 시작
            self.is_alerting[level] = True
            logger.info(f"[{level.value.upper()}] 경고 발생. 장치: {AlertDevice.PIEZO_BUZZER.value}, 지속 시간: {self.alert_duration}초")

            # 피에조 부저 명령 전송
            if not self.mock_mode:
                command = self.buzzer_commands.get(level)
                if command:
                    self.communicator.send_command(command)
                    logger.info(f"피에조 부저 명령 전송: {command}")

            self._activate_device_internal()

            # 지정된 시간 후 경고 해제 타이머 설정
            threading.Timer(self.alert_duration, self._deactivate_alert, args=[level]).start()

    def _activate_device_internal(self):
        """(내부용) 부저 장치를 활성화 상태로 변경합니다."""
        self.device_status[AlertDevice.PIEZO_BUZZER.value] = "active"

    def _deactivate_alert(self, level: AlertLevel):
        """(내부용) 특정 레벨의 경고를 비활성화합니다."""
        with self._lock:
            logger.info(f"[{level.value.upper()}] 경고 상태 초기화.")
            self.device_status[AlertDevice.PIEZO_BUZZER.value] = "idle"
            self.is_alerting[level] = False

    def trigger_medium_alarm(self, message: str = "Medium risk detected"):
        self.trigger_alert(AlertLevel.MEDIUM, message)

    def trigger_high_alarm(self, message: str = "High risk detected"):
        self.trigger_alert(AlertLevel.HIGH, message)

    def trigger_critical_alarm(self, message: str = "Critical risk detected"):
        self.trigger_alert(AlertLevel.CRITICAL, message)

    def get_all_statuses(self) -> Dict[str, str]:
        """모든 장치의 상태를 반환합니다."""
        return self.device_status

    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'mock_mode': self.mock_mode,
            'device_statuses': self.get_all_statuses()
        }