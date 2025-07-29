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
    """전원 제어 시스템 (GPIO 로직 제거 버전)"""

    def __init__(self, mock_mode: bool = True, **kwargs):
        # 라즈베리파이를 사용하지 않으므로, 항상 모의 모드처럼 동작하거나
        # 아두이노를 통한 전원 제어 로직을 여기에 추가할 수 있습니다.
        # 현재는 상태 관리와 로깅에만 집중합니다.
        self.mock_mode = True # 하드웨어 제어 로직이 없으므로 항상 True
        self.current_state = PowerState.OFF
        self._lock = threading.Lock()
        self.state_history: List[Dict] = []
        self.max_history_size = 100
        logger.info(f"전원 제어기 초기화 완료 (상태 관리 전용 모드)")

    def prevent_power_on(self, reason: str = "Safety interlock: Person in danger zone") -> bool:
        with self._lock:
            logger.info(f"[PowerController] 전원 켜짐 방지: {reason}")
            if self.current_state == PowerState.ON:
                return self._set_state_unsafe(PowerState.OFF, reason)
            return True

    def allow_power_on(self, reason: str = "Safety interlock released: Danger zone clear") -> bool:
        with self._lock:
            if self.current_state != PowerState.EMERGENCY_OFF:
                return self._set_state_unsafe(PowerState.ON, reason)
            else:
                logger.warning("비상 정지 상태에서는 전원을 켤 수 없습니다. 리셋이 필요합니다.")
                return False

    def stop_power(self, reason: str = "Critical risk detected: Immediate shutdown") -> bool:
        return self.emergency_off(reason)

    def emergency_off(self, reason: str = "비상 정지") -> bool:
        with self._lock:
            return self._set_state_unsafe(PowerState.EMERGENCY_OFF, reason)

    def _set_state_unsafe(self, new_state: PowerState, reason: str) -> bool:
        if self.current_state == new_state:
            return False

        previous_state = self.current_state
        self.current_state = new_state
        
        logger.info(f"전원 상태 변경: {previous_state.value} -> {new_state.value} (이유: {reason})")
        return True

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