from loguru import logger
import time
import threading
from typing import Dict, Optional, Callable
from enum import Enum
import serial
import serial.tools.list_ports

class SpeedState(Enum):
    """속도 상태"""
    FULL = "full"
    HALF = "half"
    STOP = "stop"

class SpeedController:
    """속도 제어 시스템 (아두이노 연동)"""

    def __init__(self, mock_mode: bool = True, port: Optional[str] = "COM9", baudrate: int = 9600):
        """
        속도 제어기를 초기화합니다.
        :param mock_mode: 모의 모드 여부. False일 경우 실제 아두이노와 통신합니다.
        :param port: 아두이노 시리얼 포트. None이면 자동으로 찾습니다.
        :param baudrate: 통신 속도 (보드레이트).
        """
        self.mock_mode = mock_mode
        self.current_speed_percent = 100  # 0-100%
        self.current_state = SpeedState.FULL
        self.speed_history = []
        self.max_history_size = 100
        self.arduino: Optional[serial.Serial] = None

        if not self.mock_mode:
            self._initialize_serial(port, baudrate)
        
        logger.info(f"속도 제어기 초기화: 모의 모드: {self.mock_mode}, 포트: {self.get_port_info() or 'N/A'}")

    def _initialize_serial(self, port: Optional[str], baudrate: int):
        """시리얼 포트를 찾아 아두이노와 연결을 초기화합니다."""
        try:
            if port is None:
                # 자동 탐지 대신 기본 포트를 사용하거나, 명시적 설정을 요구할 수 있습니다.
                logger.error("아두이노 포트가 지정되지 않았습니다. config 또는 파라미터로 포트를 명시해주세요.")
                return

            logger.info(f"아두이노 포트({port})에 {baudrate} 보드레이트로 연결을 시도합니다...")
            self.arduino = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # 아두이노가 리셋되고 시리얼 통신을 준비할 시간을 줍니다.
            logger.success(f"아두이노에 성공적으로 연결되었습니다: {self.arduino.name}")

        except serial.SerialException as e:
            logger.error(f"시리얼 포트 연결에 실패했습니다: {e}")
            self.arduino = None

    def _find_arduino_port(self) -> Optional[str]:
        """연결된 장치 목록에서 아두이노 포트를 자동으로 찾습니다."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # 아두이노는 보통 'Arduino' 또는 'CH340' 같은 문자열을 포함
            if "Arduino" in p.description or "CH340" in p.description:
                logger.info(f"아두이노 포트 발견: {p.device} ({p.description})")
                return p.device
        return None

    def set_speed(self, percent: int, reason: str = "Manual control") -> bool:
        """
        속도를 설정하고, 실제 모드일 경우 아두이노에 명령을 전송합니다.
        :param percent: 설정할 속도 (0-100%)
        :param reason: 속도 변경 이유
        """
        if not (0 <= percent <= 100):
            logger.warning(f"유효하지 않은 속도 값: {percent}. 0-100% 범위여야 합니다.")
            return False

        if self.current_speed_percent == percent:
            return False # 이미 해당 속도이면 변경하지 않음

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

        if self.mock_mode:
            logger.info(f"[모의] 속도 변경: {previous_speed}% -> {self.current_speed_percent}% (이유: {reason})")
        else:
            self._send_speed_to_arduino(self.current_speed_percent, reason)
        
        return True

    def _send_speed_to_arduino(self, percent: int, reason: str):
        """실제 아두이노에 속도 제어 명령을 전송합니다."""
        if self.arduino and self.arduino.is_open:
            # 속도(0-100%)를 아두이노의 PWM 값(0-255)으로 변환
            pwm_value = int((percent / 100) * 255)
            
            # 's[값]\n' 형태의 명령 전송 (예: 's128\n')
            command = f"s{pwm_value}\n"
            try:
                self.arduino.write(command.encode('utf-8'))
                logger.info(f"[실제] 모터 속도 제어: {percent}% (PWM: {pwm_value}), 이유: {reason}")
            except serial.SerialException as e:
                logger.error(f"아두이노에 데이터 전송 실패: {e}")
        else:
            logger.warning("아두이노가 연결되지 않아 속도를 제어할 수 없습니다.")

    def slow_down_50_percent(self, reason: str = "Safety: Person detected") -> bool:
        """속도를 50%로 감속합니다."""
        return self.set_speed(50, reason)

    def stop_conveyor(self, reason: str = "Emergency stop") -> bool:
        """컨베이어를 정지합니다."""
        return self.set_speed(0, reason)

    def resume_full_speed(self, reason: str = "Safety clear") -> bool:
        """최대 속도로 복귀합니다."""
        return self.set_speed(100, reason)

    def get_current_speed(self) -> int:
        """현재 속도(%)를 반환합니다."""
        return self.current_speed_percent

    def get_current_state(self) -> SpeedState:
        """현재 속도 상태를 반환합니다."""
        return self.current_state

    def _add_to_history(self, speed_change: Dict):
        """속도 변경을 히스토리에 추가합니다."""
        self.speed_history.append(speed_change)
        if len(self.speed_history) > self.max_history_size:
            self.speed_history.pop(0)

    def get_speed_history(self, limit: int = 10) -> list:
        """속도 변경 히스토리를 반환합니다."""
        return self.speed_history[-limit:]

    def get_port_info(self) -> Optional[str]:
        """연결된 포트 정보를 반환합니다."""
        if self.arduino and self.arduino.is_open:
            return self.arduino.name
        return None

    def get_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'current_speed_percent': self.current_speed_percent,
            'current_state': self.current_state.value,
            'mock_mode': self.mock_mode,
            'port': self.get_port_info(),
            'is_connected': self.arduino.is_open if self.arduino else False,
            'history_size': len(self.speed_history)
        }

    def close(self):
        """시리얼 연결을 닫고 자원을 해제합니다."""
        if self.arduino and self.arduino.is_open:
            self.set_speed(0, "System shutdown") # 종료 전 모터 정지
            self.arduino.close()
            logger.info(f"시리얼 포트({self.arduino.name}) 연결을 해제했습니다.")