import time
import threading
import json
import random
from typing import Optional, Dict, Any, List
from collections import deque
from loguru import logger

from core.serial_communicator import SerialCommunicator

try:
    import serial
except ImportError:
    serial = None

class SensorReader:
    """
    아두이노의 자율 제어 보고를 수신하고, 센서 데이터를 읽는 리스너 클래스.
    """
    def __init__(self, 
                 communicator: Optional[SerialCommunicator] = None, 
                 mock_mode: bool = True,
                 max_buffer_size: int = 100):
        
        if not mock_mode and communicator is None:
            raise ValueError("SensorReader는 실제 모드에서 SerialCommunicator 객체가 반드시 필요합니다.")

        self.communicator = communicator
        self.mock_mode = mock_mode
        
        self.lock = threading.Lock()
        self.is_running = False
        self.max_buffer_size = max_buffer_size

        # 센서의 최신 상태 저장
        self.latest_states: Dict[str, Dict[str, Any]] = {
            "PIR": {"value": 1, "timestamp": 0},
            "ULTRASONIC": {"value": -1, "timestamp": 0}
        }
        # 아두이노의 자율 제어 이벤트를 저장하는 큐
        self.status_event_queue: deque = deque(maxlen=50)
        
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
        """백그라운드에서 아두이노 데이터를 지속적으로 읽고 상태와 이벤트를 업데이트합니다."""
        while self.is_running:
            if self.mock_mode or self.communicator is None:
                self._update_mock_states()
                time.sleep(0.5)
                continue

            line = self.communicator.read_line()
            if not line:
                time.sleep(0.01)
                continue

            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    self._process_received_data(data)
                except json.JSONDecodeError:
                    logger.warning(f"[Sensor] JSON 파싱 실패. 원본 데이터: {line}")
            else:
                logger.debug(f"[Sensor] JSON 형식이 아닌 데이터 수신: {line}")

    def _process_received_data(self, data: Dict[str, Any]):
        """수신된 데이터를 종류에 따라 처리합니다 (센서 상태 or 자율 제어 이벤트)."""
        data_type = data.get("type")
        
        with self.lock:
            if data_type in self.latest_states:
                # Case 1: 일반 센서 데이터 (PIR, ULTRASONIC)
                value = data.get("value")
                if value is not None:
                    now = time.time()
                    self.latest_states[data_type] = {"value": value, "timestamp": now}
                    # 데이터 버퍼에도 최신 상태 기록 (기존 로직 유지)
                    self.data_buffer.append(self.read())

            elif data_type == "STATUS":
                # Case 2: 아두이노의 자율 제어 상태 보고
                logger.info(f"Arduino 자율 제어 이벤트 수신: {data}")
                self.status_event_queue.append(data)

    def _update_mock_states(self):
        """모의 모드용 상태 및 버퍼 업데이트 함수"""
        now = time.time()
        with self.lock:
            self.latest_states["PIR"] = {"value": random.choice([0, 1]), "timestamp": now}
            self.latest_states["ULTRASONIC"] = {"value": random.randint(3, 100), "timestamp": now}
            self.data_buffer.append(self.read())

    def read(self) -> Dict[str, Any]:
        """
        최신 센서 데이터를 반환합니다. '신선도' 체크 로직은 제거되었습니다.
        """
        with self.lock:
            current_states = {s_type: data.copy() for s_type, data in self.latest_states.items()}

        now = time.time()
        output_sensors = {}

        for sensor_type, state in current_states.items():
            value = state["value"]
            threshold = self.thresholds.get(sensor_type)
            
            is_alert = False
            if sensor_type == "PIR":
                is_alert = (value == 0)
            elif sensor_type == "ULTRASONIC":
                is_alert = (0 < value < threshold)

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

    def get_status_events(self) -> List[Dict[str, Any]]:
        """큐에 쌓인 아두이노의 자율 제어 상태 이벤트를 모두 가져오고 큐를 비웁니다."""
        with self.lock:
            events = list(self.status_event_queue)
            self.status_event_queue.clear()
        return events

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