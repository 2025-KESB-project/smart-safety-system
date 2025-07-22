from loguru import logger
import time
import threading
from typing import Dict, Optional, Callable
from enum import Enum

class SpeedState(Enum):
    """속도 상태"""
    FULL = "full"
    HALF = "half"
    STOP = "stop"

class SpeedController:
    """속도 제어 시스템"""

    def __init__(self, mock_mode: bool = True):
        """
        속도 제어기를 초기화합니다.
        :param mock_mode: 모의 모드 여부
        """
        self.mock_mode = mock_mode
        self.current_speed_percent = 100  # 0-100%
        self.current_state = SpeedState.FULL
        self.speed_history = []
        self.max_history_size = 100
        
        logger.info(f"속도 제어기 초기화: 모의 모드: {mock_mode}")

    def set_speed(self, percent: int, reason: str = "Manual control") -> bool:
        """
        속도를 설정합니다.
        :param percent: 설정할 속도 (0-100%)
        :param reason: 속도 변경 이유
        """
        if not (0 <= percent <= 100):
            logger.warning(f"유효하지 않은 속도 값: {percent}. 0-100% 범위여야 합니다.")
            return False

        if self.current_speed_percent == percent:
            logger.info(f"이미 {percent}% 속도입니다.")
            return False

        previous_speed = self.current_speed_percent
        self.current_speed_percent = percent
        
        if percent == 0:
            self.current_state = SpeedState.STOP
        elif percent <= 50:
            self.current_state = SpeedState.HALF
        else:
            self.current_state = SpeedState.FULL

        speed_change = {
            'from_speed': previous_speed,
            'to_speed': self.current_speed_percent,
            'from_state': self.current_state.value,
            'to_state': self.current_state.value,
            'timestamp': time.time(),
            'reason': reason
        }
        self._add_to_history(speed_change)

        if self.mock_mode:
            logger.info(f"[SpeedController] 속도 변경: {previous_speed}% -> {self.current_speed_percent}% (이유: {reason})")
        else:
            # 실제 모터 제어 로직 (PWM 등)
            logger.info(f"[SpeedController] 실제 모터 속도 제어: {self.current_speed_percent}%")
        
        return True

    def slow_down_50_percent(self, reason: str = "Safety: Person detected") -> bool:
        """
        속도를 50%로 감속합니다.
        """
        logger.info(f"[SpeedController] Slowing down to 50%: {reason}")
        return self.set_speed(50, reason)

    def stop_conveyor(self, reason: str = "Emergency stop") -> bool:
        """
        컨베이어를 정지합니다.
        """
        logger.info(f"[SpeedController] Stopping conveyor: {reason}")
        return self.set_speed(0, reason)

    def resume_full_speed(self, reason: str = "Safety clear") -> bool:
        """
        최대 속도로 복귀합니다.
        """
        logger.info(f"[SpeedController] Resuming full speed: {reason}")
        return self.set_speed(100, reason)

    def get_current_speed(self) -> int:
        """
        현재 속도(%)를 반환합니다.
        """
        return self.current_speed_percent

    def get_current_state(self) -> SpeedState:
        """
        현재 속도 상태를 반환합니다.
        """
        return self.current_state

    def _add_to_history(self, speed_change: Dict):
        """
        속도 변경을 히스토리에 추가합니다.
        """
        self.speed_history.append(speed_change)
        if len(self.speed_history) > self.max_history_size:
            self.speed_history.pop(0)

    def get_speed_history(self, limit: int = 10) -> list:
        """
        속도 변경 히스토리를 반환합니다.
        """
        return self.speed_history[-limit:]

    def get_system_status(self) -> Dict:
        """
        시스템 상태를 반환합니다.
        """
        return {
            'current_speed_percent': self.current_speed_percent,
            'current_state': self.current_state.value,
            'mock_mode': self.mock_mode,
            'history_size': len(self.speed_history)
        }
