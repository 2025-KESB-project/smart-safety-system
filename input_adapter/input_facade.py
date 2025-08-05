from .stream import VideoStream
from .preprocess import VideoPreprocessor
from .sensor import SensorReader
from typing import Optional
from loguru import logger
from core.serial_communicator import SerialCommunicator
import numpy as np

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
        # Fail-Fast: 실제 모드(mock_mode=False)에서는 communicator가 필수입니다.
        if not mock_mode and communicator is None:
            raise ValueError("InputAdapter는 실제 모드에서 SerialCommunicator 객체가 반드시 필요합니다.")

        self.use_camera = use_camera
        self.mock_mode = mock_mode

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

    def get_sensor_data(self) -> dict:
        """센서 데이터만 읽어서 반환합니다. (빠른 작업)"""
        return self.sensor.read()

    def get_frame(self) -> Optional[np.ndarray]:
        """카메라 프레임만 읽어서 반환합니다. (잠재적 블로킹 작업)"""
        if self.mock_mode:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        if self.stream:
            return self.stream.get_frame()
        return None

    def get_preprocessed_frame(self, frame: np.ndarray) -> np.ndarray:
        """주어진 프레임을 전처리하여 반환합니다."""
        return self.preprocessor.process_frame(frame)

    def get_status_events(self) -> list:
        """SensorReader로부터 아두이노의 자율 제어 상태 이벤트를 가져옵니다."""
        return self.sensor.get_status_events()

    def release(self):
        if self.stream is not None:
            self.stream.release()
        # SensorReader의 stop 메소드 호출
        self.sensor.stop()