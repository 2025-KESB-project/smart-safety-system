from .stream import VideoStream
from .preprocess import VideoPreprocessor
from .sensor import SensorReader

class InputAdapter:
    def __init__(self, camera_index=0, sensor_pin=17):
        self.stream = VideoStream(source=camera_index)
        self.preprocessor = VideoPreprocessor()
        self.sensor = SensorReader(sensor_pin=sensor_pin)

    def get_input(self):
        """카메라 프레임과 센서 데이터를 함께 가져와서 반환
            :return: dict { 'frame': 전처리된 이미지, 'raw_frame': 원본 이미지, 'sensor_data': 센서값 }
            """


        frame = self.stream.get_frames()
        preprocessed = self.preprocessor.process_frame(frame)
        sensor_data = self.sensor.read()
        return {
            'frame' : preprocessed,
            'raw_frame': frame,
            'sensor_data': sensor_data
        }

    def release(self):
        self.stream.release()