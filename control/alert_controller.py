from loguru import logger
from typing import Dict, Optional
from enum import Enum
import threading

from control.serial_communicator import SerialCommunicator

class AlertLevel(Enum):
    """경고 수준 (값은 아두이노에서 사용하는 것과 일치시킬 수 있음)"""
    NONE = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class AlertController:
    """
    상태 기반 경고 제어 시스템.
    ControlFacade에 의해 제어되며, 중복 명령을 방지합니다.
    """

    def __init__(self, communicator: Optional[SerialCommunicator], mock_mode: bool = True):
        """
        경고 제어기를 초기화합니다.
        :param communicator: 시리얼 통신 객체
        :param mock_mode: 모의 모드 여부
        """
        self.serial = communicator
        self.mock_mode = mock_mode
        self.current_alert_level = AlertLevel.NONE
        self._lock = threading.Lock()
        logger.info(f"경고 제어기 초기화 완료. 모의 모드: {self.mock_mode}")

    def trigger_alert(self, level: AlertLevel, message: str = ""):
        """
        지정된 수준의 경고를 활성화합니다.
        이 메서드는 ControlFacade에 의해 호출되며, Facade가 이미 상태 변경을
        확인했으므로 여기서는 바로 명령을 실행합니다.
        """
        if not isinstance(level, AlertLevel):
            logger.error(f"잘못된 경고 수준: {level}")
            return

        # ControlFacade에서 이미 상태 변경을 감지하고 로그를 남겼으므로,
        # 여기서는 실제 제어 로직만 수행합니다.
        with self._lock:
            if not self.mock_mode:
                # 예시: "ALERT=HIGH" 또는 "ALERT=3" 형태의 명령 전송
                command = f"ALERT={level.name}" 
                self.serial.send_command(command)
            
            # 내부 상태 업데이트
            self.current_alert_level = level

    def get_status(self) -> Dict:
        """
        현재 경고 시스템의 상태를 반환합니다.
        """
        with self._lock:
            return {
                'current_alert_level': self.current_alert_level.name,
                'is_alert_on': self.current_alert_level != AlertLevel.NONE
            }
