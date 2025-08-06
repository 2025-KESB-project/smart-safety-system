from loguru import logger
import time
from typing import Dict, Coroutine
from enum import Enum

from control.serial_communicator import SerialCommunicator

class SpeedState(Enum):
    """속도 상태"""
    FULL = "full"
    HALF = "half"
    STOP = "stop"

class SpeedController:
    """속도 제어 시스템 (아두이노 연동)"""

    def __init__(self, communicator: SerialCommunicator, mock_mode: bool = False):
        self.communicator = communicator
        self.mock_mode = mock_mode
        self.current_speed_percent = 0
        self.current_state = SpeedState.STOP
        self.speed_history = []
        self.max_history_size = 100
        
        logger.info(f"속도 제어기 초기화 완료. SerialCommunicator 사용. 모의 모드: {self.mock_mode}")

    async def set_speed(self, percent: int, reason: str = "Manual control") -> bool:
        """
        속도를 비동기적으로 설정하고, 실제 모드일 경우 아두이노에 명령을 전송합니다.
        """
        if not (0 <= percent <= 100):
            logger.warning(f"유효하지 않은 속도 값: {percent}. 0-100% 범위여야 합니다.")
            return False

        if self.current_speed_percent == percent:
            return False

        previous_speed = self.current_speed_percent
        self.current_speed_percent = percent
        
        if percent == 0:
            self.current_state = SpeedState.STOP
        elif percent <= 50:
            self.current_state = SpeedState.HALF
        else:
            self.current_state = SpeedState.FULL

        self._add_to_history({
            'from_speed': previous_speed,
            'to_speed': self.current_speed_percent,
            'timestamp': time.time(),
            'reason': reason
        })

        pwm_value = int((percent / 100) * 255)
        command = f"s{pwm_value}"
        response = await self.communicator.send_command(command)
        logger.info(f"모터 속도 제어: {previous_speed}% -> {self.current_speed_percent}% (PWM: {pwm_value}), 이유: {reason}, 응답: {response}")

        return "OK" in response

    async def slow_down_50_percent(self, reason: str = "Safety: Person detected") -> bool:
        """속도를 50%로 감속합니다."""
        return await self.set_speed(50, reason)

    async def stop_conveyor(self, reason: str = "Emergency stop") -> bool:
        """컨베이어를 정지합니다."""
        return await self.set_speed(0, reason)

    async def resume_full_speed(self, reason: str = "Safety clear") -> bool:
        """최대 속도로 복귀합니다."""
        return await self.set_speed(100, reason)

    def get_current_speed(self) -> int:
        return self.current_speed_percent

    def get_current_state(self) -> SpeedState:
        return self.current_state

    def _add_to_history(self, speed_change: Dict):
        self.speed_history.append(speed_change)
        if len(self.speed_history) > self.max_history_size:
            self.speed_history.pop(0)

    def get_speed_history(self, limit: int = 10) -> list:
        return self.speed_history[-limit:]

    async def get_status(self) -> Dict:
        is_connected = False
        if not self.mock_mode and self.communicator and self.communicator.serial:
            is_connected = self.communicator.serial.is_open

        return {
            'current_speed_percent': self.current_speed_percent,
            'current_state': self.current_state.value,
            'mock_mode': self.mock_mode,
            'port': self.communicator.port if self.communicator else None,
            'is_connected': is_connected,
            'history_size': len(self.speed_history)
        }

    async def release(self):
        """자원을 해제합니다. 종료 전 모터를 정지시킵니다."""
        logger.info("SpeedController 자원 해제. 안전을 위해 모터를 정지합니다.")
        await self.stop_conveyor("System shutdown")