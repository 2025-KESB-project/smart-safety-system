import time
import logging
import sys
import os

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from input_adapter.sensor import ArduinoController

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 제어 상수 ---
SERIAL_PORT = 'COM9'  # 사용하는 COM 포트에 맞게 수정하세요.
BAUDRATE = 9600

FULL_SPEED = 100       # 100% 속도
HALF_SPEED = 50        # 50% 속도
STOP_SPEED = 0         # 정지

PROXIMITY_THRESHOLD_SLOW = 20  # 20cm 이내 감지 시 감속
PROXIMITY_THRESHOLD_STOP = 10  # 10cm 이내 감지 시 정지

SAFE_DURATION_THRESHOLD = 5  # 5초 동안 안전 거리가 유지되면 정상 속도로 복귀

class ConveyorTester:
    def __init__(self, port, baudrate):
        self.arduino = ArduinoController(port, baudrate)
        self.current_speed = 0
        self.is_buzzer_on = False
        self.last_proximity_time = None

    def run_test(self):
        if not self.arduino.connect():
            logging.error("테스트를 시작할 수 없습니다. 아두이노 연결을 확인하세요.")
            return

        try:
            logging.info("테스트 시작: 컨베이어를 100% 속도로 가동합니다.")
            self.set_speed(FULL_SPEED)

            while True:
                sensor_data = self.arduino.read_data()
                distance = sensor_data.get('ultrasonic', 999)

                logging.info(f"수신 데이터: 거리 = {distance} cm, 현재 속도 = {self.current_speed}%")

                if distance <= PROXIMITY_THRESHOLD_STOP:
                    # 10cm 이내: 정지 및 부저 ON
                    if self.current_speed != STOP_SPEED:
                        logging.warning(f"[위험] {distance}cm 이내 물체 감지! 모터를 정지하고 부저를 켭니다.")
                        self.set_speed(STOP_SPEED)
                        self.set_buzzer(True)
                    self.last_proximity_time = time.time()

                elif distance <= PROXIMITY_THRESHOLD_SLOW:
                    # 20cm 이내: 50% 감속
                    if self.current_speed != HALF_SPEED:
                        logging.warning(f"[경고] {distance}cm 이내 물체 감지! 모터를 50%로 감속합니다.")
                        self.set_speed(HALF_SPEED)
                        self.set_buzzer(False) # 정지 상태가 아니므로 부저는 끔
                    self.last_proximity_time = time.time()

                else:
                    # 안전 거리: 정상 속도로 복귀 조건 확인
                    if self.current_speed != FULL_SPEED:
                        if self.last_proximity_time is None:
                            self.last_proximity_time = time.time() # 타이머 초기화
                        
                        safe_time = time.time() - self.last_proximity_time
                        if safe_time >= SAFE_DURATION_THRESHOLD:
                            logging.info(f"{SAFE_DURATION_THRESHOLD}초 동안 안전 거리 확보. 모터를 100%로 복귀합니다.")
                            self.set_speed(FULL_SPEED)
                            self.set_buzzer(False)
                            self.last_proximity_time = None # 타이머 리셋
                        else:
                            logging.info(f"안전 거리 유지 시간: {safe_time:.1f}초. 복귀 대기 중...")
                    
                    # 부저가 켜져 있었다면 끈다.
                    if self.is_buzzer_on:
                        self.set_buzzer(False)

                time.sleep(0.2) # 아두이노 전송 간격과 맞춤

        except KeyboardInterrupt:
            logging.info("사용자에 의해 테스트가 중단되었습니다.")
        finally:
            logging.info("테스트 종료: 모든 장치를 정지합니다.")
            self.set_speed(STOP_SPEED)
            self.set_buzzer(False)
            self.arduino.disconnect()

    def set_speed(self, speed_percent):
        if self.current_speed != speed_percent:
            self.arduino.set_motor_speed(speed_percent)
            self.current_speed = speed_percent
            logging.info(f"명령 전송: 모터 속도를 {speed_percent}%로 설정")

    def set_buzzer(self, state):
        if self.is_buzzer_on != state:
            self.arduino.control_buzzer(state)
            self.is_buzzer_on = state
            logging.info(f"명령 전송: 부저를 {'ON' if state else 'OFF'}으로 설정")

if __name__ == "__main__":
    tester = ConveyorTester(SERIAL_PORT, BAUDRATE)
    tester.run_test()