from .stream import VideoStream
from .preprocess import VideoPreprocessor
from .sensor import SensorReader
from typing import Optional
from loguru import logger

from control.serial_communicator import SerialCommunicator

class InputAdapter:
    def __init__(self, 
                 communicator: Optional[SerialCommunicator] = None, 
                 use_camera: bool = True, 
                 camera_index: int = 0, 
                 mock_mode: bool = False):
        """
        InputAdapter는 카메라와 센서로부터 입력을 받아 전처리된 데이터를 반환합니다.
        이제 SerialCommunicator를 주입받아 SensorReader에게 전달합니다.
        """
        self.use_camera = use_camera
        # communicator가 없거나 mock_mode가 True이면 전체가 모의 모드로 작동
        self.mock_mode = mock_mode or (communicator is None)

        if self.use_camera and not self.mock_mode:
            self.stream = VideoStream(source=camera_index)
        else:
            self.stream = None
            logger.info("[InputAdapter] 카메라를 사용하지 않거나 모의 모드입니다.")

        self.preprocessor = VideoPreprocessor()
        
        # SensorReader 초기화 시, 주입받은 communicator 전달
        self.sensor = SensorReader(
            communicator=communicator,
            mock_mode=self.mock_mode
        )

    def get_input(self):
        """카메라 프레임과 센서 데이터를 함께 가져와서 반환합니다."""
        # 1. 센서 데이터는 항상 읽어옵니다.
        sensor_data = self.sensor.read()
        raw_frame = None
        preprocessed_frame = None

        # 2. 모의 모드일 경우, 더미 프레임을 생성합니다.
        if self.mock_mode:
            import numpy as np
            raw_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            preprocessed_frame = self.preprocessor.process_frame(raw_frame)
        # 3. 실제 카메라 스트림이 활성화된 경우에만 프레임을 가져옵니다.
        elif self.stream is not None:
            raw_frame = self.stream.get_frame()
            if raw_frame is not None:
                preprocessed_frame = self.preprocessor.process_frame(raw_frame)
            else:
                logger.warning("InputAdapter: 스트림에서 유효한 프레임을 얻지 못했습니다.")
        
        # 최종적으로 수집된 데이터를 반환합니다.
        # raw_frame이 None일 수도 있지만, sensor_data는 항상 존재합니다.
        return {
            'frame': preprocessed_frame,
            'raw_frame': raw_frame,
            'sensor_data': sensor_data
        }

    def release(self):
        if self.stream is not None:
            self.stream.release()
        # SensorReader의 stop 메소드 호출
        self.sensor.stop()