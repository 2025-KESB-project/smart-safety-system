from loguru import logger
from control.serial_communicator import SerialCommunicator


class PowerController:
    """
    릴레이 모듈을 직접 제어하여 시스템의 주 전원을 ON/OFF합니다.
    SerialCommunicator를 통해 아두이노에 'p1'(ON) 또는 'p0'(OFF) 명령을 전송합니다.
    """

    def __init__(self, communicator: SerialCommunicator, mock_mode: bool = True):
        self.communicator = communicator
        self.mock_mode = mock_mode
        self._is_power_on = False
        logger.info(f"전원 제어기 초기화 완료. SerialCommunicator 사용. 모의 모드: {self.mock_mode}")

    async def power_on(self, reason: str = "System start"):
        """릴레이를 켜서 컨베이어 시스템에 전원을 공급합니다."""
        if not self._is_power_on:
            logger.success(f"전원 공급 시작. 이유: {reason}")
            response = await self.communicator.send_command("p1")
            if "OK" in response:
                self._is_power_on = True
            logger.debug(f"Power ON response: {response}")
        else:
            logger.info("이미 전원이 공급된 상태입니다.")

    async def power_off(self, reason: str = "System stop"):
        """릴레이를 꺼서 컨베이어 시스템의 전원을 차단합니다. (LOTO)"""
        if self._is_power_on:
            logger.warning(f"전원 공급 차단. 이유: {reason}")
            response = await self.communicator.send_command("p0")
            if "OK" in response:
                self._is_power_on = False
            logger.debug(f"Power OFF response: {response}")
        else:
            logger.info("이미 전원이 차단된 상태입니다.")

    async def prevent_power_on(self, reason: str = "Safety interlock: Person in danger zone"):
        """LOTO의 핵심 로직. 전원을 차단합니다."""
        await self.power_off(reason)

    def allow_power_on(self, reason: str = "Safety interlock released: Danger zone clear"):
        """전원 투입을 허용합니다."""
        logger.info(f"전원 투입 '허용' 상태로 변경. 이유: {reason}")

    async def stop_power(self, reason: str = "Critical risk detected: Immediate shutdown"):
        """위험 상황 발생 시 전원을 즉시 차단합니다."""
        logger.critical(f"[EMERGENCY] 전원 즉시 차단! 이유: {reason}")
        await self.power_off(reason=f"EMERGENCY STOP: {reason}")

    def is_power_on(self) -> bool:
        """현재 전원이 켜져 있는지 확인합니다."""
        return self._is_power_on

    async def get_status(self) -> dict:
        """PowerController의 현재 상태를 반환합니다."""
        return {
            "is_power_on": self._is_power_on,
            "mock_mode": self.mock_mode
        }

    async def release(self):
        """PowerController의 자원을 해제합니다."""
        logger.info("PowerController 자원 해제. 안전을 위해 전원을 차단합니다.")
        await self.power_off("System shutdown")