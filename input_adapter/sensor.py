import time
import threading
import json
import random
from typing import Optional, Dict, Any, List
from collections import deque
from loguru import logger

from control.serial_communicator import SerialCommunicator

try:
    import serial
except ImportError:
    serial = None

class SensorReader:
    """
    아두이노 또는 모의 데이터를 통해 센서 데이터를 읽는 지능형 클래스.
    이제 SerialCommunicator를 주입받아 시리얼 통신을 처리합니다.
    """
    STALE_THRESHOLD_SECONDS = 1.5

    def __init__(self, 
                 communicator: Optional[SerialCommunicator] = None, 
                 mock_mode: bool = True,
                 max_buffer_size: int = 100):
        
        self.communicator = communicator
        # communicator가 없거나, communicator가 모의 모드이면 SensorReader도 모의 모드로 작동
        self.mock_mode = mock_mode or (communicator is None) or communicator.mock_mode
        
        self.lock = threading.Lock()
        self.is_running = False
        self.max_buffer_size = max_buffer_size

        self.latest_states: Dict[str, Dict[str, Any]] = {
            "PIR": {"value": 1, "timestamp": 0},
            "ULTRASONIC": {"value": -1, "timestamp": 0}
        }
        self.data_buffer: deque = deque(maxlen=self.max_buffer_size)
        self.thresholds = {
            "PIR": 0,
            "ULTRASONIC": 5
        }
        
        if self.mock_mode:
            logger.info("[SensorReader] 통신 모듈이 없거나 모의 모드이므로, 모의 모드로 실행됩니다.")
        else:
            logger.info("[SensorReader] 실제 통신 모듈을 사용하여 실행됩니다.")

        self.start()

    def _background_worker(self):
        """백그라운드에서 데이터를 지속적으로 읽고 상태와 버퍼를 업데이트합니다."""
        while self.is_running:
            if self.mock_mode or self.communicator is None:
                self._update_mock_states()
                time.sleep(0.5)
                continue

            line = self.communicator.read_line()
            if not line:
                time.sleep(0.01) # 데이터가 없을 경우 CPU 사용량 방지를 위해 짧은 대기
                continue

            if line.startswith("{") and line.endswith("}"):
                try:
                    sensor_data = json.loads(line)
                    self._process_received_data(sensor_data)
                except json.JSONDecodeError:
                    logger.warning(f"[Sensor] JSON 파싱 실패. 원본 데이터: {line}")
            else:
                logger.debug(f"[Sensor] JSON 형식이 아닌 데이터 수신: {line}")

    def _process_received_data(self, sensor_data: Dict[str, Any]):
        """수신된 데이터를 처리하여 latest_states와 data_buffer를 모두 업데이트합니다."""
        sensor_type = sensor_data.get("type")
        value = sensor_data.get("value")
        
        # 유효한 센서 타입인지 확인
        if not (sensor_type and value is not None and sensor_type in self.latest_states):
            return

        now = time.time()
        with self.lock:
            # 1. 최신 상태 업데이트
            self.latest_states[sensor_type] = {"value": value, "timestamp": now}
            
            # 2. 데이터 버퍼에 추가 (read()와 동일한 형식으로)
            # read()를 호출하여 현재의 완전한 센서 상태를 가져와 버퍼에 저장
            self.data_buffer.append(self.read())

    def _update_mock_states(self):
        """모의 모드용 상태 및 버퍼 업데이트 함수"""
        now = time.time()
        with self.lock:
            # PIR 모의 데이터: 0 (감지) 또는 1 (미감지)
            self.latest_states["PIR"] = {"value": random.choice([0, 1]), "timestamp": now}
            # ULTRASONIC 모의 데이터: 3cm ~ 100cm
            self.latest_states["ULTRASONIC"] = {"value": random.randint(3, 100), "timestamp": now}
            
            # 데이터 버퍼에 추가
            self.data_buffer.append(self.read())

    def read(self) -> Dict[str, Any]:
        """
        '신선도'가 보장된 최신 센서 데이터를 반환합니다.
        """
        with self.lock:
            # 현재 상태를 안전하게 복사
            fresh_states = {s_type: data.copy() for s_type, data in self.latest_states.items()}

        now = time.time()
        output_sensors = {}

        for sensor_type, state in fresh_states.items():
            is_stale = (now - state["timestamp"]) > self.STALE_THRESHOLD_SECONDS
            value = state["value"]
            threshold = self.thresholds.get(sensor_type)


            if is_stale:
                # 데이터가 오래되었으면 센서 타입에 따라 기본/안전 값으로 되돌림
                if sensor_type == "PIR":
                    value = 1 # PIR은 미감지(1)가 안전한 기본값
                elif sensor_type == "ULTRASONIC":
                    value = -1 # 초음파는 비정상(-1)이 안전한 기본값
            
            # is_alert 계산 로직
            is_alert = False
            if sensor_type == "PIR":
                is_alert = (value == 0) # PIR은 0일 때 감지 (alert)
            elif sensor_type == "ULTRASONIC":
                is_alert = (0 < value < threshold) # 초음파는 0보다 크고 임계값 미만일 때 경고

            output_sensors[sensor_type] = {
                "value": value,
                "unit": "binary" if sensor_type == "PIR" else "cm",
                "is_alert": is_alert,
                "threshold": threshold
            }

        return {
            "timestamp": now,
            "sensors": output_sensors
        }

    def start(self):
        """백그라운드 모니터링 스레드를 시작합니다."""
        if self.is_running: return
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._background_worker, daemon=True)
        self.monitor_thread.start()
        print("[SensorReader] 백그라운드 모니터링 시작.")

    def stop(self):
        """백그라운드 모니터링 스레드를 안전하게 중지합니다."""
        if not self.is_running: return
        self.is_running = False
        # SerialCommunicator의 생명주기는 외부에서 관리하므로, 여기서는 닫지 않습니다.
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
        logger.info("[SensorReader] 백그라운드 모니터링 중지.")

    def __del__(self):
        """객체 소멸 시 스레드를 확실히 종료합니다."""
        self.stop()

    def get_alert_status(self) -> Dict[str, bool]:
        """최신 센서 데이터 기반으로 알림 상태를 반환합니다."""
        latest_data = self.read()
        return {st: sd["is_alert"] for st, sd in latest_data["sensors"].items()}

    def get_sensor_history(self, sensor_type: str, limit: int = 10) -> List[Dict]:
        """데이터 버퍼에서 특정 센서의 히스토리를 반환합니다."""
        history = []
        with self.lock:
            buffer_copy = list(self.data_buffer)
        
        for data in reversed(buffer_copy):
            if sensor_type in data["sensors"]:
                sensor_info = data["sensors"][sensor_type]
                history.append({
                    "timestamp": data["timestamp"],
                    "value": sensor_info["value"],
                    "is_alert": sensor_info["is_alert"]
                })
            if len(history) >= limit:
                break
        return list(reversed(history))

    def set_threshold(self, sensor_type: str, threshold: float):
        """센서 임계값을 설정합니다."""
        if sensor_type in self.thresholds:
            self.thresholds[sensor_type] = threshold
        else:
            print(f"알 수 없는 센서 타입: {sensor_type}")

    def get_system_status(self) -> Dict:
        """현재 시스템 상태를 반환합니다."""
        with self.lock:
            buffer_size = len(self.data_buffer)
            latest_states_copy = self.latest_states.copy()

        return {
            "mock_mode": self.mock_mode,
            "serial_port": self.communicator.port if self.communicator and not self.communicator.mock_mode else None,
            "is_running": self.is_running,
            "buffer_size": buffer_size,
            "thresholds": self.thresholds,
            "latest_states": latest_states_copy
        }