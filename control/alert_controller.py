from loguru import logger
import time
from typing import Dict, List, Tuple
from enum import Enum
import threading

class AlertLevel(Enum):
    """경고 수준"""
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertDevice(Enum):
    """경고 장치 종류"""
    SIREN = "siren"
    WARNING_LIGHT = "warning_light"
    SPEAKER = "speaker"

class AlertController:
    """통합 경고 제어 시스템"""

    def __init__(self, mock_mode: bool = True):
        """
        경고 제어기를 초기화합니다.
        :param mock_mode: 모의 모드 여부
        """
        self.mock_mode = mock_mode
        self.device_status: Dict[AlertDevice, Dict] = {device: {"status": "idle"} for device in AlertDevice}
        self.is_alerting: Dict[AlertLevel, bool] = {level: False for level in AlertLevel} # 경고 상태 플래그
        self._lock = threading.Lock()

        # 위험 수준별 경고 장치 및 지속 시간 설정
        self.alert_configs: Dict[AlertLevel, Tuple[List[AlertDevice], int]] = {
            AlertLevel.MEDIUM: ([AlertDevice.WARNING_LIGHT], 5),
            AlertLevel.HIGH: ([AlertDevice.WARNING_LIGHT, AlertDevice.SPEAKER], 10),
            AlertLevel.CRITICAL: ([AlertDevice.SIREN, AlertDevice.WARNING_LIGHT, AlertDevice.SPEAKER], 15)
        }
        
        logger.info(f"통합 경고 제어기 초기화: 모의 모드: {self.mock_mode}")

    def trigger_alert(self, level: AlertLevel, message: str = ""):
        """
        지정된 위험 수준에 따라 경고를 발생시킵니다.
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
            devices_to_activate, duration = self.alert_configs[level]
            logger.info(f"[{level.value.upper()}] 경고 발생. 활성화 장치: {[d.value for d in devices_to_activate]}, 지속 시간: {duration}초")

            for device in devices_to_activate:
                self._activate_device_internal(device, duration, message)

            # 지정된 시간 후 경고 해제 타이머 설정
            threading.Timer(duration, self._deactivate_alert, args=[level, devices_to_activate]).start()

    def _activate_device_internal(self, device: AlertDevice, duration: float, message: str):
        """(내부용) 특정 경고 장치를 활성화합니다."""
        self.device_status[device] = {
            "status": "active",
            "start_time": time.time(),
            "duration": duration,
            "message": message
        }
        if not self.mock_mode:
            # 실제 장치 제어 로직
            pass

    def _deactivate_alert(self, level: AlertLevel, devices: List[AlertDevice]):
        """(내부용) 특정 레벨의 경고와 관련된 모든 장치를 비활성화합니다."""
        with self._lock:
            logger.info(f"[{level.value.upper()}] 경고 종료. 비활성화 장치: {[d.value for d in devices]}")
            for device in devices:
                self.device_status[device] = {"status": "idle"}
                if not self.mock_mode:
                    # 실제 장치 비활성화 로직
                    pass
            self.is_alerting[level] = False

    def trigger_medium_alarm(self, message: str = "Medium risk detected"):
        self.trigger_alert(AlertLevel.MEDIUM, message)

    def trigger_high_alarm(self, message: str = "High risk detected"):
        self.trigger_alert(AlertLevel.HIGH, message)

    def trigger_critical_alarm(self, message: str = "Critical risk detected"):
        self.trigger_alert(AlertLevel.CRITICAL, message)

    

    def get_device_status(self, device: AlertDevice) -> Dict:
        """특정 장치의 상태를 반환합니다."""
        return self.device_status.get(device, {"status": "not_found"})

    def get_all_statuses(self) -> Dict[str, Dict]:
        """모든 장치의 상태를 반환합니다."""
        return {device.value: status for device, status in self.device_status.items()}

    def get_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'is_alert_on': any(self.is_alerting.values()),
            'mock_mode': self.mock_mode,
            'device_statuses': self.get_all_statuses()
        }