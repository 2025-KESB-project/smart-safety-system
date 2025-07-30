
from loguru import logger

class PowerController:
    """
    컨베이어의 물리적 전원 상태(On/Off)를 관리하는 클래스.
    자신의 상태(self.is_on)를 직접 소유하고 제어합니다.
    """
    def __init__(self, mock_mode: bool = True):
        """
        PowerController를 초기화합니다.
        :param mock_mode: True일 경우, 실제 하드웨어(GPIO)를 제어하지 않습니다.
        """
        self.is_on: bool = False
        self.mock_mode: bool = mock_mode
        logger.info(f"PowerController 초기화됨. Mock 모드: {self.mock_mode}, 초기 상태: OFF")

    def turn_on(self, reason: str = "명령 수신") -> bool:
        """컨베이어 전원을 켭니다."""
        if not self.is_on:
            self.is_on = True
            logger.info(f"전원 ON. (사유: {reason})")
            if not self.mock_mode:
                self._control_hardware(True)
            return True
        return False

    def turn_off(self, reason: str = "명령 수신") -> bool:
        """컨베이어 전원을 끕니다."""
        if self.is_on:
            self.is_on = False
            logger.warning(f"전원 OFF. (사유: {reason})")
            if not self.mock_mode:
                self._control_hardware(False)
            return True
        return False

    def get_status(self) -> dict:
        """현재 전원 상태를 반환합니다."""
        return {"conveyor_is_on": self.is_on}

    def _control_hardware(self, power_on: bool):
        """
        (내부 함수) 실제 하드웨어(예: GPIO)를 제어합니다.
        """
        # 여기에 RPi.GPIO 등을 사용한 실제 제어 코드가 들어갑니다.
        pin_state = "HIGH" if power_on else "LOW"
        logger.info(f"[HARDWARE] GPIO 핀 상태를 {pin_state}로 변경합니다.")
        pass
