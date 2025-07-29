# 실제 센서 연동 전까지 mock용
import random
import time
import threading
from typing import Optional, Dict, Any, List


class SensorReader:
    """다양한 센서 데이터를 읽는 클래스"""

    def __init__(self, sensor_pin: Optional[int] = None,
                 sensor_types=None,
                 mock_mode: bool = True):
        """
        센서 리더를 초기화합니다.
        :param sensor_pin: 센서 핀 번호 (Raspberry Pi GPIO)
        :param sensor_types: 센서 타입 리스트
        :param mock_mode: 모의 모드 여부
        """
        self.sensor_pin = sensor_pin
        self.mock_mode = mock_mode
        # 'conveyor_operating' 센서 타입을 기본값에 추가
        self.sensor_types = sensor_types or ["touch", "distance", "temperature", "humidity", "conveyor_operating"]
        self.is_running = False
        self.data_buffer = []
        self.max_buffer_size = 100

        # 센서별 임계값 설정
        self.thresholds = {
            "touch": 0.5,
            "distance": 50.0,  # cm
            "temperature": 35.0,  # Celsius
            "humidity": 80.0,  # %
            "conveyor_operating": 0.5  # 1 for operating, 0 for stopped
        }

        # GPIO 초기화 (실제 하드웨어 연결 시)
        if not mock_mode and sensor_pin is not None:
            self._initialize_gpio()

    def _initialize_gpio(self):
        """GPIO를 초기화합니다."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            if self.sensor_pin is not None:
                GPIO.setup(self.sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                raise ValueError("sensor_pin must not be None when initializing GPIO.")
            print(f"GPIO 핀 {self.sensor_pin} 초기화 완료")
        except ImportError:
            print("RPi.GPIO 모듈을 찾을 수 없습니다. 모의 모드로 실행됩니다.")
            self.mock_mode = True
        except Exception as e:
            print(f"GPIO 초기화 실패: {e}")
            self.mock_mode = True

    def read(self) -> Dict[str, Any]:
        """
        센서 데이터를 읽습니다.
        :return: 센서 데이터 딕셔너리
        """
        if self.mock_mode:
            return self._read_mock_data()
        else:
            return self._read_real_data()

    def _read_mock_data(self) -> Dict[str, Any]:
        """모의 센서 데이터를 생성합니다."""
        data = {
            "timestamp": time.time(),
            "sensors": {}
        }

        for sensor_type in self.sensor_types:
            if sensor_type == "touch":
                value = random.uniform(0, 1)
                is_alert = value > self.thresholds["touch"]
            elif sensor_type == "distance":
                value = random.uniform(10, 100)
                is_alert = value < self.thresholds["distance"]
            elif sensor_type == "temperature":
                value = random.uniform(20, 40)
                is_alert = value > self.thresholds["temperature"]
            elif sensor_type == "humidity":
                value = random.uniform(30, 90)
                is_alert = value > self.thresholds["humidity"]
            elif sensor_type == "conveyor_operating":
                # 테스트를 위해 컨베이어는 항상 작동 중(1)이라고 가정
                value = 1
                is_alert = False  # 이 센서는 상태 정보 제공이 목적
            else:
                value = random.uniform(0, 100)
                is_alert = False

            data["sensors"][sensor_type] = {
                "value": round(value, 2),
                "unit": self._get_unit(sensor_type),
                "is_alert": False,  # 테스트 중에는 항상 False로 설정
                "threshold": self.thresholds.get(sensor_type, 0)
            }

        # 데이터 버퍼에 저장
        self._add_to_buffer(data)

        return data

    def _read_real_data(self) -> Dict[str, Any]:
        """실제 센서 데이터를 읽습니다."""
        data = {
            "timestamp": time.time(),
            "sensors": {}
        }

        try:
            import RPi.GPIO as GPIO

            # 터치 센서 읽기
            if "touch" in self.sensor_types:
                if self.sensor_pin is None:
                    raise ValueError("sensor_pin must not be None when reading real data.")
                touch_value = GPIO.input(self.sensor_pin)
                data["sensors"]["touch"] = {
                    "value": touch_value,
                    "unit": "binary",
                    "is_alert": touch_value > self.thresholds["touch"],
                    "threshold": self.thresholds["touch"]
                }

            # 다른 센서들도 여기에 추가 가능
            # 예: I2C, SPI 센서 등

        except Exception as e:
            print(f"실제 센서 읽기 실패: {e}")
            return self._read_mock_data()

        self._add_to_buffer(data)
        return data

    def _get_unit(self, sensor_type: str) -> str:
        """센서 타입에 따른 단위를 반환합니다."""
        units = {
            "touch": "binary",
            "distance": "cm",
            "temperature": "°C",
            "humidity": "%",
            "pressure": "hPa",
            "light": "lux",
            "conveyor_operating": "binary"
        }
        return units.get(sensor_type, "unknown")
    
    def _add_to_buffer(self, data: Dict):
        """데이터를 버퍼에 추가합니다."""
        self.data_buffer.append(data)
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer.pop(0)
    
    def get_alert_status(self) -> Dict[str, bool]:
        """각 센서의 알림 상태를 반환합니다."""
        current_data = self.read()
        alerts = {}
        
        for sensor_type, sensor_data in current_data["sensors"].items():
            alerts[sensor_type] = sensor_data["is_alert"]
        
        return alerts
    
    def get_sensor_history(self, sensor_type: str, limit: int = 10) -> List[Dict]:
        """특정 센서의 히스토리를 반환합니다."""
        history = []
        
        for data in self.data_buffer[-limit:]:
            if sensor_type in data["sensors"]:
                history.append({
                    "timestamp": data["timestamp"],
                    "value": data["sensors"][sensor_type]["value"],
                    "is_alert": data["sensors"][sensor_type]["is_alert"]
                })
        
        return history
    
    def set_threshold(self, sensor_type: str, threshold: float):
        """센서 임계값을 설정합니다."""
        if sensor_type in self.thresholds:
            self.thresholds[sensor_type] = threshold
            print(f"{sensor_type} 센서 임계값을 {threshold}로 설정했습니다.")
        else:
            print(f"알 수 없는 센서 타입: {sensor_type}")
    
    def start_continuous_monitoring(self, callback=None, interval: float = 1.0):
        """연속 모니터링을 시작합니다."""
        self.is_running = True
        
        def monitor():
            while self.is_running:
                data = self.read()
                if callback:
                    callback(data)
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_continuous_monitoring(self):
        """연속 모니터링을 중지합니다."""
        self.is_running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
    
    def get_system_status(self) -> Dict:
        """시스템 상태를 반환합니다."""
        return {
            "mock_mode": self.mock_mode,
            "sensor_pin": self.sensor_pin,
            "sensor_types": self.sensor_types,
            "is_running": self.is_running,
            "buffer_size": len(self.data_buffer),
            "thresholds": self.thresholds
        }
