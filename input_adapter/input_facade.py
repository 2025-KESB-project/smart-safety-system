from .stream import VideoStream
from .preprocess import VideoPreprocessor
from .sensor import SensorReader
import numpy as np
from loguru import logger

class InputAdapter:
    def __init__(self, config: dict):
        """
        InputAdapter는 카메라와 센서로부터 입력을 받아 전처리된 데이터를 반환하는 역할을 합니다.
        :param config: 입력 장치 관련 설정을 담은 딕셔너리
        """
        self.mock_mode = config.get('mock_mode', False)
        camera_index = config.get('camera_index', 0)
        sensor_pin = config.get('sensor_pin') # 없으면 None

        if not self.mock_mode:
            # VideoStream 초기화 시 camera_index를 source로 전달
            self.stream = VideoStream(source=camera_index)
        else:
            self.stream = None
        self.preprocessor = VideoPreprocessor()
        # SensorReader 초기화
        self.sensor = SensorReader(sensor_pin=sensor_pin if sensor_pin is not None else 0)
        logger.info("InputAdapter 초기화 완료.")

    def get_frame(self):
        """카메라로부터 원본 프레임을 가져옵니다."""
        if self.mock_mode or self.stream is None:
            # 모의 모드에서는 더미 프레임 반환
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        return self.stream.get_frame()

    def get_sensor_data(self):
        """센서 데이터를 읽어옵니다."""
        return self.sensor.read()

    def get_status_events(self):
        """
        아두이노 등 외부 장치로부터의 자율 제어 이벤트를 확인합니다.
        예: 비상 정지 버튼, 수동 조작 등
        현재는 플레이스홀더 구현이며, 향후 시리얼 통신 프로토콜에 맞춰 확장해야 합니다.
        """
        # TODO: SensorReader에서 실제 이벤트 파싱 로직 구현 필요
        # 지금은 빈 리스트를 반환하여 background_worker와의 호환성을 맞춥니다.
        return []

    def get_input(self):
        """
        [기존 호환성 유지] 카메라 프레임과 센서 데이터를 함께 가져와서 반환합니다.
        """
        raw_frame = self.get_frame()
        if raw_frame is not None:
            preprocessed_frame = self.preprocessor.process_frame(raw_frame)
            sensor_data = self.get_sensor_data()
            return {
                'frame': preprocessed_frame,
                'raw_frame': raw_frame,
                'sensor_data': sensor_data
            }
        return None

    def release(self):
        """리소스(카메라 등)를 해제합니다."""
        if self.stream is not None:
            self.stream.release()
            logger.info("카메라 리소스를 해제했습니다.")
