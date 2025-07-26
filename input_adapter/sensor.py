import serial
import json
import time

class ArduinoController:
    """
    아두이노와 시리얼 통신을 통해 센서 데이터를 읽고, 액추에이터를 제어하는 클래스.
    """
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        ArduinoController를 초기화합니다.

        Args:
            port (str): 아두이노가 연결된 COM 포트 (예: 'COM3' 또는 '/dev/ttyUSB0').
            baudrate (int): 시리얼 통신 속도.
            timeout (int): 읽기 타임아웃 (초).
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.last_data = {"ultrasonic": 999}

    def connect(self):
        """아두이노와 시리얼 연결을 설정합니다."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # 아두이노 리셋 및 안정화 대기
            print(f"성공: {self.port} 포트를 통해 아두이노와 연결되었습니다.")
            # 초기 버퍼에 쌓인 메시지 비우기
            self.ser.flushInput()
            return True
        except serial.SerialException as e:
            print(f"에러: 아두이노 연결에 실패했습니다 ({self.port}). {e}")
            return False

    def disconnect(self):
        """시리얼 연결을 종료합니다."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("정보: 아두이노와의 연결이 종료되었습니다.")

    def send_command(self, command):
        """
        아두이노에 제어 명령을 전송합니다.

        Args:
            command (str): 전송할 명령어 (예: 's128', 'b1').
        """
        if self.ser and self.ser.is_open:
            self.ser.write(f"{command}\n".encode('utf-8'))
        else:
            print("경고: 명령을 보낼 수 없습니다. 아두이노가 연결되지 않았습니다.")

    def set_motor_speed(self, speed_percent):
        """
        모터 속도를 퍼센트(0-100)로 설정합니다.

        Args:
            speed_percent (int): 0부터 100 사이의 속도 값.
        """
        pwm_val = int((speed_percent / 100) * 255)
        if not (0 <= pwm_val <= 255):
            print(f"경고: 속도 값({speed_percent}%)이 범위를 벗어났습니다. 0-100 사이로 조정됩니다.")
            pwm_val = max(0, min(255, pwm_val))
        self.send_command(f"s{pwm_val}")

    def control_buzzer(self, state):
        """
        부저를 켜거나 끕니다.

        Args:
            state (bool): True는 켜기, False는 끄기.
        """
        self.send_command(f"b{1 if state else 0}")

    def read_data(self):
        """
        아두이노로부터 들어오는 JSON 데이터를 읽고 파싱합니다.

        Returns:
            dict: 센서 데이터 딕셔너리 (예: {"ultrasonic": 15}).
                  읽기/파싱 에러 발생 시 마지막으로 수신한 데이터를 반환합니다.
        """
        if not (self.ser and self.ser.is_open):
            return self.last_data

        try:
            line = self.ser.readline().decode('utf-8').strip()
            if line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                self.last_data = data
                return data
        except (json.JSONDecodeError, UnicodeDecodeError):
            # JSON 형식이 아닌 데이터(예: 아두이노의 시작 메시지)는 무시
            pass
        except serial.SerialException as e:
            print(f"에러: 시리얼 포트 읽기 중 문제 발생. {e}")
            # 연결이 끊겼을 수 있으므로 빈 데이터 반환
            return {"ultrasonic": 999}
            
        return self.last_data