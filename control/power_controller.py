from loguru import logger
import time
import threading
from typing import Dict, Optional, Callable, List
from enum import Enum

class PowerState(Enum):
    """전원 상태"""
    ON = "on"
    OFF = "off"
    EMERGENCY_OFF = "emergency_off"
    MAINTENANCE = "maintenance"

class PowerController:
    """전원 제어 시스템"""
    
    def __init__(self, gpio_pin: int = 18, mock_mode: bool = True):
        """
        전원 제어기를 초기화합니다.

        Args:
            gpio_pin: 제어할 GPIO 핀 번호
            mock_mode: 모의 모드 여부. True이면 GPIO를 제어하지 않습니다.
        """
        self.gpio_pin = gpio_pin
        self.mock_mode = mock_mode
        self.current_state = PowerState.OFF
        self.is_running = False  # 모니터링 스레드 실행 상태

        # 스레드 안전성을 위한 Lock
        self._lock = threading.Lock()

        # 상태 변경 히스토리 및 콜백
        self.state_history: List[Dict] = []
        self.max_history_size = 100
        self.state_change_callbacks: List[Callable] = []

        # 모니터링 스레드 객체
        self.monitor_thread: Optional[threading.Thread] = None

        if not self.mock_mode:
            self._setup_gpio()

        logger.info(f"전원 제어기 초기화 완료: GPIO 핀 {self.gpio_pin}, 모의 모드: {self.mock_mode}")

    def _setup_gpio(self):
        """GPIO 핀을 설정합니다."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)  # 경고 메시지 비활성화
            GPIO.setmode(GPIO.BCM)  # BCM 핀 번호 모드 사용
            GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info(f"GPIO {self.gpio_pin}번 핀을 출력으로 설정했습니다.")
        except (ImportError, RuntimeError) as e:
            logger.error(f"GPIO 설정 중 오류 발생: {e}")
            self.mock_mode = True
            logger.warning("GPIO 오류로 인해 모의 모드로 강제 전환합니다.")

    def prevent_power_on(self, reason: str = "Safety interlock: Person in danger zone") -> bool:
        """전원이 켜지는 것을 방지합니다 (LOTO 기능)."""
        logger.info(f"[PowerController] Preventing power on: {reason}")
        # 전원이 켜져 있다면 끄고, 켜지지 않도록 유지
        if self.current_state == PowerState.ON:
            return self._set_state(PowerState.OFF, reason)
        elif self.current_state == PowerState.EMERGENCY_OFF:
            logger.info("Already in emergency off state, power on prevented.")
            return True
        else:
            logger.info("Power is already off or in maintenance, power on prevented.")
            return True

    def allow_power_on(self, reason: str = "Safety interlock released: Danger zone clear") -> bool:
        """전원 투입을 허용합니다."""
        logger.info(f"[PowerController] Allowing power on: {reason}")
        # 비상 정지 상태가 아니라면 전원 켬
        if self.current_state != PowerState.EMERGENCY_OFF:
            return self._set_state(PowerState.ON, reason)
        else:
            logger.warning("Cannot allow power on while in emergency off state. Reset required.")
            return False

    def stop_power(self, reason: str = "Critical risk detected: Immediate shutdown") -> bool:
        """전원을 즉시 중단합니다 (비상 정지)."""
        logger.info(f"[PowerController] Stopping power: {reason}")
        return self.emergency_off()

    def turn_on(self) -> bool:
        """전원을 켭니다."""
        return self._set_state(PowerState.ON, "수동 켜기")

    def turn_off(self) -> bool:
        """전원을 끕니다."""
        return self._set_state(PowerState.OFF, "수동 끄기")

    def emergency_off(self) -> bool:
        """비상 정지를 수행합니다."""
        return self._set_state(PowerState.EMERGENCY_OFF, "비상 정지")

    def maintenance_mode(self) -> bool:
        """유지보수 모드로 전환합니다."""
        return self._set_state(PowerState.MAINTENANCE, "유지보수 모드")

    def _set_state(self, new_state: PowerState, reason: str) -> bool:
        """상태를 변경합니다."""
        if self.current_state == new_state:
            logger.info(f"이미 {new_state.value} 상태입니다.")
            return False
        
        # 상태 변경 기록
        state_change = {
            'from_state': self.current_state.value,
            'to_state': new_state.value,
            'timestamp': time.time(),
            'reason': reason
        }
        
        # 이전 상태 저장
        previous_state = self.current_state
        
        # 상태 변경
        self.current_state = new_state
        
        # GPIO 제어
        if not self.mock_mode:
            self._control_gpio(new_state)
        
        # 히스토리에 추가
        self._add_to_history(state_change)
        
        # 콜백 실행
        self._execute_callbacks(previous_state, new_state, reason)
        
        logger.info(f"전원 상태 변경: {previous_state.value} -> {new_state.value} (이유: {reason})")
        return True

    def _control_gpio(self, state: PowerState):
        """GPIO를 제어합니다."""
        try:
            import RPi.GPIO as GPIO
            
            if state == PowerState.ON:
                GPIO.output(self.gpio_pin, GPIO.HIGH)
            elif state == PowerState.OFF:
                GPIO.output(self.gpio_pin, GPIO.LOW)
            elif state == PowerState.EMERGENCY_OFF:
                GPIO.output(self.gpio_pin, GPIO.LOW)
                # 추가적인 비상 정지 로직
                self._emergency_shutdown()
            elif state == PowerState.MAINTENANCE:
                GPIO.output(self.gpio_pin, GPIO.LOW)
                
        except Exception as e:
            logger.error(f"GPIO 제어 중 오류: {e}")

    def _emergency_shutdown(self):
        """비상 정지 절차를 수행합니다."""
        logger.critical("비상 정지 절차 실행 중...")
        
        # 1. 모든 모터 정지
        self._stop_all_motors()
        
        # 2. 안전 장치 활성화
        self._activate_safety_devices()
        
        # 3. 알림 발송
        self._send_emergency_notification()
        
        logger.critical("비상 정지 절차 완료")

    def _stop_all_motors(self):
        """모든 모터를 정지시킵니다."""
        logger.info("모든 모터 정지")
        # 실제 구현에서는 모터 제어 시스템과 연동

    def _activate_safety_devices(self):
        """안전 장치를 활성화합니다."""
        logger.info("안전 장치 활성화")
        # 실제 구현에서는 안전 장치와 연동

    def _send_emergency_notification(self):
        """비상 알림을 발송합니다."""
        logger.info("비상 알림 발송")
        # 실제 구현에서는 알림 시스템과 연동

    def get_current_state(self) -> PowerState:
        """현재 상태를 반환합니다."""
        return self.current_state

    def is_power_on(self) -> bool:
        """전원이 켜져 있는지 확인합니다."""
        return self.current_state == PowerState.ON

    def is_emergency_off(self) -> bool:
        """비상 정지 상태인지 확인합니다."""
        return self.current_state == PowerState.EMERGENCY_OFF

    def register_state_change_callback(self, callback: Callable):
        """상태 변경 콜백을 등록합니다."""
        self.state_change_callbacks.append(callback)

    def _execute_callbacks(self, from_state: PowerState, to_state: PowerState, reason: str):
        """상태 변경 콜백을 실행합니다."""
        for callback in self.state_change_callbacks:
            try:
                callback(from_state, to_state, reason)
            except Exception as e:
                logger.error(f"상태 변경 콜백 실행 중 오류: {e}")

    def _add_to_history(self, state_change: Dict):
        """상태 변경을 히스토리에 추가합니다."""
        self.state_history.append(state_change)
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)

    def get_state_history(self, limit: int = 10) -> list:
        """상태 변경 히스토리를 반환합니다."""
        return self.state_history[-limit:]

    def get_power_statistics(self) -> Dict:
        """전원 통계를 반환합니다."""
        stats = {
            'current_state': self.current_state.value,
            'total_changes': len(self.state_history),
            'state_counts': {state.value: 0 for state in PowerState},
            'last_change_time': None
        }
        
        for change in self.state_history:
            stats['state_counts'][change['to_state']] += 1
        
        if self.state_history:
            stats['last_change_time'] = self.state_history[-1]['timestamp']
        
        return stats

    def auto_control_based_on_risk(self, risk_level: str, mode_config: Dict):
        """위험도에 따른 자동 제어를 수행합니다."""
        auto_stop = mode_config.get('auto_stop', False)
        
        if risk_level == 'critical':
            self.emergency_off()
        elif risk_level == 'high' and auto_stop:
            self.turn_off()
        elif risk_level == 'low' and self.current_state == PowerState.OFF:
            # 안전한 상황에서 자동 복구
            self.turn_on()

    def start_monitoring(self, interval: float = 1.0):
        """전원 상태 모니터링을 시작합니다."""
        self.is_running = True
        
        def monitor():
            while self.is_running:
                # 전원 상태 확인
                if not self.mock_mode:
                    self._check_power_status()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """전원 상태 모니터링을 중지합니다."""
        self.is_running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

    def _check_power_status(self):
        """전원 상태를 확인합니다."""
        try:
            import RPi.GPIO as GPIO
            current_gpio_state = GPIO.input(self.gpio_pin)
            
            # GPIO 상태와 내부 상태가 일치하지 않는 경우
            expected_gpio_state = GPIO.HIGH if self.current_state == PowerState.ON else GPIO.LOW
            if current_gpio_state != expected_gpio_state:
                logger.warning(f"GPIO 상태 불일치 감지: 예상={expected_gpio_state}, 실제={current_gpio_state}")
                
        except Exception as e:
            logger.error(f"전원 상태 확인 중 오류: {e}")

    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'current_state': self.current_state.value,
            'gpio_pin': self.gpio_pin,
            'mock_mode': self.mock_mode,
            'is_running': self.is_running,
            'history_size': len(self.state_history)
        }


