from loguru import logger
import time
from typing import Dict

class WarningController:
    """기타 경고 장치 제어 시스템 (예: 추가 경고등, 사이렌 등)"""

    def __init__(self, mock_mode: bool = True):
        """
        경고 장치 제어기를 초기화합니다.
        :param mock_mode: 모의 모드 여부
        """
        self.mock_mode = mock_mode
        self.device_status = {"status": "idle"}
        logger.info(f"경고 장치 제어기 초기화: 모의 모드: {mock_mode}")

    def activate_device(self, device_id: str, duration: float = 5.0, message: str = "") -> bool:
        """
        특정 경고 장치를 활성화합니다.
        :param device_id: 장치 ID (예: "siren", "extra_light")
        :param duration: 활성화 지속 시간 (초)
        :param message: 표시할 메시지
        """
        logger.info(f"[WarningDevice] Activating device '{device_id}' for {duration} seconds with message: '{message}'")
        self.device_status = {"status": "active", "device_id": device_id, "message": message, "start_time": time.time(), "duration": duration}
        
        if self.mock_mode:
            logger.info(f"[WarningDevice] Mock mode: Device '{device_id}' activated.")
        else:
            # 실제 장치 제어 로직 구현
            pass

        # 일정 시간 후 비활성화 스케줄링
        # threading.Timer(duration, self.deactivate_device, args=[device_id]).start()
        return True

    def deactivate_device(self, device_id: str) -> bool:
        """
        특정 경고 장치를 비활성화합니다.
        :param device_id: 장치 ID
        """
        logger.info(f"[WarningDevice] Deactivating device '{device_id}'")
        if self.device_status.get("device_id") == device_id:
            self.device_status = {"status": "idle"}
        
        if self.mock_mode:
            logger.info(f"[WarningDevice] Mock mode: Device '{device_id}' deactivated.")
        else:
            # 실제 장치 비활성화 로직 구현
            pass
        return True

    def get_device_status(self, device_id: str = None) -> Dict:
        """
        특정 장치 또는 모든 장치의 상태를 반환합니다.
        """
        if device_id and self.device_status.get("device_id") == device_id:
            return self.device_status
        elif not device_id:
            return self.device_status # 현재는 단일 장치만 가정
        return {"status": "not_found"}

    def get_system_status(self) -> Dict:
        """
        시스템 상태를 반환합니다.
        """
        return {
            'mock_mode': self.mock_mode,
            'device_status': self.device_status
        }
