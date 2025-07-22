from .stream import VideoStream
from .preprocess import VideoPreprocessor
from .sensor import SensorReader

class InputAdapter:
    def __init__(self, camera_index=0, sensor_pin=None, mock_mode=False):
        """
        InputAdapter는 카메라와 센서로부터 입력을 받아 전처리된 데이터를 반환하는 역할을 합니다.
        :param camera_index: 카메라 인덱스 (기본값: 0)
        :param sensor_pin: 센서 핀
        :param mock_mode: 모의 모드 여부 (카메라 없이 테스트)
        """
        self.mock_mode = mock_mode
        if not mock_mode:
            self.stream = VideoStream(source=camera_index)
        else:
            self.stream = None
        self.preprocessor = VideoPreprocessor()
        self.sensor = SensorReader(sensor_pin=sensor_pin if sensor_pin is not None else 0)

    def get_input(self):
        """카메라 프레임과 센서 데이터를 함께 가져와서 반환
            :return: dict { 'frame': 전처리된 이미지, 'raw_frame': 원본 이미지, 'sensor_data': 센서값 }
            """
        if self.mock_mode:
            # 모의 모드에서는 더미 데이터 반환
            import numpy as np
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            preprocessed = self.preprocessor.process_frame(dummy_frame)
            sensor_data = self.sensor.read()
            return {
                'frame': preprocessed,
                'raw_frame': dummy_frame,
                'sensor_data': sensor_data
            }
        
        if self.stream is not None:
            frame = self.stream.get_frame()
            if frame is not None:
                preprocessed = self.preprocessor.process_frame(frame)
                sensor_data = self.sensor.read()
                return {
                            'frame': preprocessed,
                    'raw_frame': frame,
                    'sensor_data': sensor_data
                }
        return None

    def release(self):
        if self.stream is not None:
            self.stream.release()