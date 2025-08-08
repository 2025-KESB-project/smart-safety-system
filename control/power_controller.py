from loguru import logger
from core.serial_communicator import SerialCommunicator


class PowerController:
    """
    릴레이 모듈을 직접 제어하여 시스템의 주 전원을 ON/OFF합니다.
    SerialCommunicator를 통해 아두이노에 'p1'(ON) 또는 'p0'(OFF) 명령을 전송합니다.
    NO 연결상태: 전원과 릴레이의 상태가 동일하다
    """

    def __init__(self, communicator: SerialCommunicator, mock_mode: bool = True):
        self.communicator = communicator
        self.mock_mode = mock_mode
        self._is_power_on = False  # 실제 전원 상태 (릴레이 상태)
        logger.info(f"전원 제어기 초기화 완료. SerialCommunicator 사용. 모의 모드: {self.mock_mode}")

    def power_on(self, reason: str = "System start"):
        """
        릴레이를 켜서 컨베이어 시스템에 전원을 공급합니다.
        """
        if not self._is_power_on:
            logger.success(f"전원 공급 시작. 이유: {reason}")
            self.communicator.send_command("p1")
            self._is_power_on = True
        else:
            logger.info("이미 전원이 공급된 상태입니다.")

    def power_off(self, reason: str = "System stop"):
        """
        릴레이를 꺼서 컨베이어 시스템의 전원을 차단합니다. (LOTO)
        """
        if self._is_power_on:
            logger.warning(f"전원 공급 차단. 이유: {reason}")
            self.communicator.send_command("p0")
            self._is_power_on = False
        else:
            logger.info("이미 전원이 차단된 상태입니다.")

    # 기존 메소드 이름 호환성을 위해 유지
    def prevent_power_on(self, reason: str = "Safety interlock: Person in danger zone"):
        """LOTO의 핵심 로직. 전원을 차단합니다."""
        self.power_off(reason)

    def allow_power_on(self, reason: str = "Safety interlock released: Danger zone clear"):
        """
        전원 투입을 허용합니다.
        실제로 전원을 켜지는 않고, 다음 `power_on` 명령이 실행될 수 있도록 상태를 준비합니다.
        (현재 구현에서는 별도 로직이 필요 없지만, 개념적으로 분리)
        """
        logger.info(f"전원 투입 '허용' 상태로 변경. 이유: {reason}")
        # self.power_on()을 여기서 호출하지 않음에 유의.
        # 제어는 상위 로직 (API 등)에서 명시적으로 이루어져야 함.

    def stop_power(self, reason: str = "Critical risk detected: Immediate shutdown"):
        """위험 상황 발생 시 전원을 즉시 차단합니다."""
        logger.critical(f"[EMERGENCY] 전원 즉시 차단! 이유: {reason}")
        self.power_off(reason=f"EMERGENCY STOP: {reason}")

    def is_power_on(self) -> bool:
        """현재 전원이 켜져 있는지 확인합니다."""
        return self._is_power_on

    def get_status(self) -> dict:
        """PowerController의 현재 상태를 반환합니다."""
        return {
            "is_power_on": self._is_power_on,
            "mock_mode": self.mock_mode
        }

    def release(self):
        """
        PowerController의 자원을 해제합니다.
        시스템 종료 시 안전을 위해 전원을 차단합니다.
        """
        logger.info("PowerController 자원 해제. 안전을 위해 전원을 차단합니다.")
        self.power_off("System shutdown")
