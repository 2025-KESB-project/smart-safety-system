from loguru import logger
import time
import threading
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """알림 타입"""
    VISUAL = "visual"      # 시각적 알림 (경광등)
    AUDIO = "audio"        # 음향 알림 (부저)
    TEXT = "text"          # 텍스트 알림
    SYSTEM = "system"      # 시스템 알림

@dataclass
class Alert:
    """알림 정보"""
    level: AlertLevel
    type: AlertType
    message: str
    timestamp: float
    duration: float = 5.0  # 알림 지속 시간 (초)
    is_active: bool = True

class AlertController:
    """알림 제어 시스템"""
    
    def __init__(self, gpio_warning_light: int = 24, gpio_buzzer: int = 25, mock_mode: bool = True):
        """
        알림 제어기를 초기화합니다.
        :param gpio_warning_light: 경광등 GPIO 핀
        :param gpio_buzzer: 부저 GPIO 핀
        :param mock_mode: 모의 모드 여부
        """
        self.gpio_warning_light = gpio_warning_light
        self.gpio_buzzer = gpio_buzzer
        self.mock_mode = mock_mode
        self.active_alerts = []
        self.alert_history = []
        self.max_history_size = 100
        self.is_running = False
        
        # 알림 콜백
        self.alert_callbacks = []
        
        # GPIO 초기화
        if not mock_mode:
            self._initialize_gpio()
        
        logger.info(f"알림 제어기 초기화: 경광등 핀 {gpio_warning_light}, 부저 핀 {gpio_buzzer}, 모의 모드: {mock_mode}")

    def trigger_critical_alarm(self, message: str = "Critical alarm triggered!"):
        """최고 위험 알람을 발생시킵니다."""
        logger.critical(f"[AlertController] Triggering CRITICAL alarm: {message}")
        self.send_alert(level=AlertLevel.CRITICAL.value, messages=[message], alert_type="system")

    def trigger_high_alarm(self, message: str = "High alarm triggered!"):
        """높은 위험 알람을 발생시킵니다.""" 
        logger.error(f"[AlertController] Triggering HIGH alarm: {message}")
        self.send_alert(level=AlertLevel.HIGH.value, messages=[message], alert_type="system")

    def trigger_medium_alarm(self, message: str = "Medium alarm triggered!"):
        """중간 위험 알람을 발생시킵니다. (WARNING 레벨로 매핑)"""
        logger.warning(f"[AlertController] Triggering MEDIUM alarm: {message}")
        self.send_alert(level=AlertLevel.WARNING.value, messages=[message], alert_type="system")

    def _initialize_gpio(self):
        """GPIO를 초기화합니다."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_warning_light, GPIO.OUT)
            GPIO.setup(self.gpio_buzzer, GPIO.OUT)
            GPIO.output(self.gpio_warning_light, GPIO.LOW)
            GPIO.output(self.gpio_buzzer, GPIO.LOW)
            logger.info(f"GPIO 핀 초기화 완료: 경광등 {self.gpio_warning_light}, 부저 {self.gpio_buzzer}")
        except ImportError:
            logger.warning("RPi.GPIO 모듈을 찾을 수 없습니다. 모의 모드로 실행됩니다.")
            self.mock_mode = True
        except Exception as e:
            logger.error(f"GPIO 초기화 실패: {e}")
            self.mock_mode = True

    def send_alert(self, level: str, messages: List[str] = None, alert_type: str = "all"):
        """
        알림을 발송합니다.
        :param level: 알림 레벨
        :param messages: 알림 메시지 리스트
        :param alert_type: 알림 타입 (visual, audio, text, all)
        """
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            logger.error(f"유효하지 않은 알림 레벨: {level}")
            return False
        
        messages = messages or [f"{level.upper()} 알림"]
        
        for message in messages:
            alert = Alert(
                level=alert_level,
                type=self._get_alert_type(alert_type),
                message=message,
                timestamp=time.time()
            )
            
            # 알림 발송
            success = self._send_single_alert(alert)
            
            if success:
                # 활성 알림에 추가
                self.active_alerts.append(alert)
                
                # 히스토리에 추가
                self._add_to_history(alert)
                
                # 콜백 실행
                self._execute_callbacks(alert)
                
                # 자동 정리 스케줄링
                threading.Timer(alert.duration, self._remove_alert, args=[alert]).start()
        
        return True

    def _get_alert_type(self, alert_type: str) -> AlertType:
        """알림 타입을 결정합니다."""
        if alert_type == "visual":
            return AlertType.VISUAL
        elif alert_type == "audio":
            return AlertType.AUDIO
        elif alert_type == "text":
            return AlertType.TEXT
        else:
            return AlertType.SYSTEM

    def _send_single_alert(self, alert: Alert) -> bool:
        """단일 알림을 발송합니다."""
        try:
            if alert.type == AlertType.VISUAL:
                return self._send_visual_alert(alert)
            elif alert.type == AlertType.AUDIO:
                return self._send_audio_alert(alert)
            elif alert.type == AlertType.TEXT:
                return self._send_text_alert(alert)
            elif alert.type == AlertType.SYSTEM:
                return self._send_system_alert(alert)
            else:
                return False
        except Exception as e:
            logger.error(f"알림 발송 중 오류: {e}")
            return False

    def _send_visual_alert(self, alert: Alert) -> bool:
        """시각적 알림을 발송합니다."""
        if self.mock_mode:
            logger.info(f"🔴 시각적 알림: {alert.message} (레벨: {alert.level.value})")
            return True
        
        try:
            import RPi.GPIO as GPIO
            
            # 알림 레벨에 따른 깜빡임 패턴
            if alert.level == AlertLevel.CRITICAL:
                pattern = [1, 0, 1, 0, 1, 0]  # 빠른 깜빡임
            elif alert.level == AlertLevel.HIGH:
                pattern = [1, 0, 1, 0]  # 중간 깜빡임
            else:
                pattern = [1, 0]  # 느린 깜빡임
            
            def blink():
                for state in pattern * 3:  # 3회 반복
                    GPIO.output(self.gpio_warning_light, GPIO.HIGH if state else GPIO.LOW)
                    time.sleep(0.5)
                GPIO.output(self.gpio_warning_light, GPIO.LOW)
            
            threading.Thread(target=blink, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"시각적 알림 발송 실패: {e}")
            return False

    def _send_audio_alert(self, alert: Alert) -> bool:
        """음향 알림을 발송합니다."""
        if self.mock_mode:
            logger.info(f"🔊 음향 알림: {alert.message} (레벨: {alert.level.value})")
            return True
        
        try:
            import RPi.GPIO as GPIO
            
            # 알림 레벨에 따른 비프음 패턴
            if alert.level == AlertLevel.CRITICAL:
                beep_count = 5
                beep_duration = 0.2
            elif alert.level == AlertLevel.HIGH:
                beep_count = 3
                beep_duration = 0.3
            else:
                beep_count = 2
                beep_duration = 0.5
            
            def beep():
                for _ in range(beep_count):
                    GPIO.output(self.gpio_buzzer, GPIO.HIGH)
                    time.sleep(beep_duration)
                    GPIO.output(self.gpio_buzzer, GPIO.LOW)
                    time.sleep(0.1)
            
            threading.Thread(target=beep, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"음향 알림 발송 실패: {e}")
            return False

    def _send_text_alert(self, alert: Alert) -> bool:
        """텍스트 알림을 발송합니다."""
        logger.info(f"📝 텍스트 알림: {alert.message} (레벨: {alert.level.value})")
        # 실제 구현에서는 SMS, 이메일, 웹훅 등으로 발송
        return True

    def _send_system_alert(self, alert: Alert) -> bool:
        """시스템 알림을 발송합니다."""
        # 모든 타입의 알림을 발송
        visual_success = self._send_visual_alert(alert)
        audio_success = self._send_audio_alert(alert)
        text_success = self._send_text_alert(alert)
        
        return visual_success or audio_success or text_success

    def _remove_alert(self, alert: Alert):
        """알림을 제거합니다."""
        if alert in self.active_alerts:
            self.active_alerts.remove(alert)
            alert.is_active = False

    def clear_all_alerts(self):
        """모든 활성 알림을 제거합니다."""
        self.active_alerts.clear()
        
        # GPIO 출력 정리
        if not self.mock_mode:
            try:
                import RPi.GPIO as GPIO
                GPIO.output(self.gpio_warning_light, GPIO.LOW)
                GPIO.output(self.gpio_buzzer, GPIO.LOW)
            except Exception as e:
                logger.error(f"GPIO 정리 중 오류: {e}")

    def get_active_alerts(self) -> List[Dict]:
        """활성 알림 목록을 반환합니다."""
        return [{
            'level': alert.level.value,
            'type': alert.type.value,
            'message': alert.message,
            'timestamp': alert.timestamp,
            'duration': alert.duration,
            'is_active': alert.is_active
        } for alert in self.active_alerts]

    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """알림 히스토리를 반환합니다."""
        return [{
            'level': alert.level.value,
            'type': alert.type.value,
            'message': alert.message,
            'timestamp': alert.timestamp,
            'duration': alert.duration,
            'is_active': alert.is_active
        } for alert in self.alert_history[-limit:]]

    def register_alert_callback(self, callback: Callable):
        """알림 콜백을 등록합니다."""
        self.alert_callbacks.append(callback)

    def _execute_callbacks(self, alert: Alert):
        """알림 콜백을 실행합니다."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"알림 콜백 실행 중 오류: {e}")

    def _add_to_history(self, alert: Alert):
        """알림을 히스토리에 추가합니다."""
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history_size:
            self.alert_history.pop(0)

    def get_alert_statistics(self) -> Dict:
        """알림 통계를 반환합니다."""
        stats = {
            'total_alerts': len(self.alert_history),
            'active_alerts': len(self.active_alerts),
            'level_counts': {level.value: 0 for level in AlertLevel},
            'type_counts': {type.value: 0 for type in AlertType},
            'last_alert_time': None
        }
        
        for alert in self.alert_history:
            stats['level_counts'][alert.level.value] += 1
            stats['type_counts'][alert.type.value] += 1
        
        if self.alert_history:
            stats['last_alert_time'] = self.alert_history[-1].timestamp
        
        return stats

    def start_monitoring(self, interval: float = 1.0):
        """알림 모니터링을 시작합니다."""
        self.is_running = True
        
        def monitor():
            while self.is_running:
                # 만료된 알림 정리
                current_time = time.time()
                expired_alerts = [
                    alert for alert in self.active_alerts
                    if current_time - alert.timestamp > alert.duration
                ]
                
                for alert in expired_alerts:
                    self._remove_alert(alert)
                
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """알림 모니터링을 중지합니다."""
        self.is_running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            'gpio_warning_light': self.gpio_warning_light,
            'gpio_buzzer': self.gpio_buzzer,
            'mock_mode': self.mock_mode,
            'is_running': self.is_running,
            'active_alerts_count': len(self.active_alerts),
            'history_size': len(self.alert_history)
        }


