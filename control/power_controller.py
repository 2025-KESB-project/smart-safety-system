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
        self.gpio_pin = gpio_pin
        self.mock_mode = mock_mode
        self.current_state = PowerState.OFF
        self.is_running = False
        self._lock = threading.Lock()
        self.state_history: List[Dict] = []
        self.max_history_size = 100
        self.state_change_callbacks: List[Callable] = []
        self.monitor_thread: Optional[threading.Thread] = None

        if not self.mock_mode:
            self._setup_gpio()

        logger.info(f"전원 제어기 초기화 완료: GPIO 핀 {self.gpio_pin}, 모의 모드: {self.mock_mode}")

    def _setup_gpio(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info(f"GPIO {self.gpio_pin}번 핀을 출력으로 설정했습니다.")
        except (ImportError, RuntimeError) as e:
            logger.error(f"GPIO 설정 중 오류 발생: {e}")
            self.mock_mode = True
            logger.warning("GPIO 오류로 인해 모의 모드로 강제 전환합니다.")

    def prevent_power_on(self, reason: str = "Safety interlock: Person in danger zone") -> bool:
        with self._lock:
            logger.info(f"[PowerController] Preventing power on: {reason}")
            if self.current_state == PowerState.ON:
                return self._set_state_unsafe(PowerState.OFF, reason)
            elif self.current_state == PowerState.EMERGENCY_OFF:
                logger.info("Already in emergency off state, power on prevented.")
                return True
            else:
                logger.info("Power is already off or in maintenance, power on prevented.")
                return True

    def allow_power_on(self, reason: str = "Safety interlock released: Danger zone clear") -> bool:
        with self._lock:
            logger.info(f"[PowerController] Allowing power on: {reason}")
            if self.current_state != PowerState.EMERGENCY_OFF:
                return self._set_state_unsafe(PowerState.ON, reason)
            else:
                logger.warning("Cannot allow power on while in emergency off state. Reset required.")
                return False

    def stop_power(self, reason: str = "Critical risk detected: Immediate shutdown") -> bool:
        return self.emergency_off(reason)

    def turn_on(self, reason: str = "수동 켜기") -> bool:
        with self._lock:
            return self._set_state_unsafe(PowerState.ON, reason)

    def turn_off(self, reason: str = "수동 끄기") -> bool:
        with self._lock:
            return self._set_state_unsafe(PowerState.OFF, reason)

    def emergency_off(self, reason: str = "비상 정지") -> bool:
        with self._lock:
            return self._set_state_unsafe(PowerState.EMERGENCY_OFF, reason)

    def maintenance_mode(self, reason: str = "유지보수 모드") -> bool:
        with self._lock:
            return self._set_state_unsafe(PowerState.MAINTENANCE, reason)

    def _set_state_unsafe(self, new_state: PowerState, reason: str) -> bool:
        if self.current_state == new_state:
            logger.info(f"이미 {new_state.value} 상태입니다.")
            return False
        
        state_change = {
            'from_state': self.current_state.value,
            'to_state': new_state.value,
            'timestamp': time.time(),
            'reason': reason
        }
        
        previous_state = self.current_state
        self.current_state = new_state
        
        if not self.mock_mode:
            self._control_gpio(new_state)
        
        self._add_to_history(state_change)
        self._execute_callbacks(previous_state, new_state, reason)
        
        logger.info(f"전원 상태 변경: {previous_state.value} -> {new_state.value} (이유: {reason})")
        return True

    def _control_gpio(self, state: PowerState):
        try:
            import RPi.GPIO as GPIO
            if state == PowerState.ON:
                GPIO.output(self.gpio_pin, GPIO.HIGH)
            else:
                GPIO.output(self.gpio_pin, GPIO.LOW)
            
            if state == PowerState.EMERGENCY_OFF:
                self._emergency_shutdown()
                
        except Exception as e:
            logger.error(f"GPIO 제어 중 오류: {e}")

    def _emergency_shutdown(self):
        logger.critical("비상 정지 절차 실행 중...")
        self._stop_all_motors()
        self._activate_safety_devices()
        self._send_emergency_notification()
        logger.critical("비상 정지 절차 완료")

    def _stop_all_motors(self):
        logger.info("모든 모터 정지")

    def _activate_safety_devices(self):
        logger.info("안전 장치 활성화")

    def _send_emergency_notification(self):
        logger.info("비상 알림 발송")

    def get_current_state(self) -> PowerState:
        with self._lock:
            return self.current_state

    def is_power_on(self) -> bool:
        with self._lock:
            return self.current_state == PowerState.ON

    def is_emergency_off(self) -> bool:
        with self._lock:
            return self.current_state == PowerState.EMERGENCY_OFF

    def register_state_change_callback(self, callback: Callable):
        with self._lock:
            self.state_change_callbacks.append(callback)

    def _execute_callbacks(self, from_state: PowerState, to_state: PowerState, reason: str):
        for callback in self.state_change_callbacks:
            try:
                callback(from_state, to_state, reason)
            except Exception as e:
                logger.error(f"상태 변경 콜백 실행 중 오류: {e}")

    def _add_to_history(self, state_change: Dict):
        self.state_history.append(state_change)
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)

    def get_state_history(self, limit: int = 10) -> list:
        with self._lock:
            return self.state_history[-limit:]

    def get_power_statistics(self) -> Dict:
        with self._lock:
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
        with self._lock:
            auto_stop = mode_config.get('auto_stop', False)
            
            if risk_level == 'critical':
                self.emergency_off("Critical risk detected")
            elif risk_level == 'high' and auto_stop:
                self.turn_off("High risk detected")
            elif risk_level == 'low' and self.current_state == PowerState.OFF:
                self.turn_on("Safe condition, auto-recovering")

    def start_monitoring(self, interval: float = 1.0):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
                self.monitor_thread.start()
                logger.info("전원 상태 모니터링 시작.")

    def _monitor_loop(self, interval: float):
        while self.is_running:
            if not self.mock_mode:
                self._check_power_status()
            time.sleep(interval)

    def stop_monitoring(self):
        with self._lock:
            if self.is_running:
                self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            logger.info("전원 상태 모니터링 중지.")

    def _check_power_status(self):
        try:
            import RPi.GPIO as GPIO
            with self._lock:
                current_gpio_state = GPIO.input(self.gpio_pin)
                expected_gpio_state = GPIO.HIGH if self.current_state == PowerState.ON else GPIO.LOW
                if current_gpio_state != expected_gpio_state:
                    logger.warning(f"GPIO 상태 불일치 감지: 예상={expected_gpio_state}, 실제={current_gpio_state}")
        except Exception as e:
            logger.error(f"전원 상태 확인 중 오류: {e}")

    def get_system_status(self) -> Dict:
        with self._lock:
            return {
                'current_state': self.current_state.value,
                'gpio_pin': self.gpio_pin,
                'mock_mode': self.mock_mode,
                'is_running': self.is_running,
                'history_size': len(self.state_history)
            }