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
        """
        if not isinstance(level, AlertLevel):
            logger.error(f"잘못된 경고 수준: {level}")
            return

        devices_to_activate, duration = self.alert_configs[level]
        logger.info(f"[{level.value.upper()}] 경고 발생. 활성화 장치: {[d.value for d in devices_to_activate]}, 지속 시간: {duration}초")

        for device in devices_to_activate:
            self.activate_device(device, duration, message)

    def trigger_medium_alarm(self, message: str = "Medium risk detected"):
        self.trigger_alert(AlertLevel.MEDIUM, message)

    def trigger_high_alarm(self, message: str = "High risk detected"):
        self.trigger_alert(AlertLevel.HIGH, message)

    def trigger_critical_alarm(self, message: str = "Critical risk detected"):
        self.trigger_alert(AlertLevel.CRITICAL, message)

    def activate_device(self, device: AlertDevice, duration: float, message: str) -> bool:
        """특정 경고 장치를 활성화합니다."""
        with self._lock:
            logger.info(f"장치 활성화: '{device.value}', 지속 시간: {duration}초, 메시지: '{message}'")
            self.device_status[device] = {
                "status": "active",
                "start_time": time.time(),
                "duration": duration,
                "message": message
            }

            if self.mock_mode:
                logger.info(f"모의 모드: 장치 '{device.value}' 활성화됨.")
            else:
                # 실제 장치 제어 로직 구현 (예: GPIO 제어)
                pass
            
            # 지정된 시간 후 비활성화
            threading.Timer(duration, self.deactivate_device, args=[device]).start()
            return True

    def deactivate_device(self, device: AlertDevice) -> bool:
        """특정 경고 장치를 비활성화합니다."""
        with self._lock:
            if self.device_status[device]["status"] == "active":
                logger.info(f"장치 비활성화: '{device.value}'")
                self.device_status[device] = {"status": "idle"}
                
                if self.mock_mode:
                    logger.info(f"모의 모드: 장치 '{device.value}' 비활성화됨.")
                else:
                    # 실제 장치 비활성화 로직 구현
                    pass
                return True
            return False

    def get_device_status(self, device: AlertDevice) -> Dict:
        """특정 장치의 상태를 반환합니다."""
        return self.device_status.get(device, {"status": "not_found"})

    def get_all_statuses(self) -> Dict[str, Dict]:
        """모든 장치의 상태를 반환합니다."""
        return {device.value: status for device, status in self.device_status.items()}

    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'mock_mode': self.mock_mode,
            'device_statuses': self.get_all_statuses()
        }