# 실제 센서 연동 전까지 mock용
import random

class SensorReader:
    def __init__(self, sensor_pin=0):
        self.sensor_pin = sensor_pin
        pass

    def read(self):
        #mock sensor data
        return {
            "touched" : random.uniform(0, 1),
        }
