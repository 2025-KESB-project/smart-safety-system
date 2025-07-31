import serial
import time
from loguru import logger
from typing import Optional

class SerialCommunicator:
    """
    아두이노와의 시리얼 통신을 전담하는 클래스입니다.
    SpeedController와 PowerController가 이 클래스의 인스턴스를 공유하여 사용합니다.
    """

    def __init__(self, port: str, baud_rate: int, mock_mode: bool = True):
        self.port = port
        self.baud_rate = baud_rate
        self.mock_mode = mock_mode
        self.serial: Optional[serial.Serial] = None

        if not self.mock_mode:
            self._initialize_serial()

    def _initialize_serial(self):
        """시리얼 포트 연결을 초기화합니다."""
        try:
            # 포트가 이미 열려있으면 닫고 다시 엽니다.
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            logger.info(f"시리얼 포트 {self.port}에 {self.baud_rate}bps로 연결을 시도합니다...")
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # 아두이노가 리셋될 시간을 줍니다.
            logger.success(f"시리얼 포트 {self.port} 연결 성공.")
            # 연결 후 아두이노로부터 초기 메시지 읽기 (버퍼 비우기)
            initial_message = self.serial.read_all().decode(errors='ignore').strip()
            if initial_message:
                logger.debug(f"Arduino says: {initial_message}")

        except serial.SerialException as e:
            logger.error(f"시리얼 포트 {self.port}에 연결할 수 없습니다: {e}")
            logger.error("모의 모드로 전환합니다. 실제 하드웨어 제어가 이루어지지 않습니다.")
            self.mock_mode = True
            self.serial = None

    def send_command(self, command: str):
        """아두이노에 명령어를 전송합니다."""
        if self.mock_mode or not self.serial or not self.serial.is_open:
            logger.info(f"[MOCK] 시리얼 명령어 전송: {command}")
            return

        try:
            full_command = f"{command}\n"
            self.serial.write(full_command.encode('utf-8'))
            logger.debug(f"시리얼 명령어 전송: {command}")
            # time.sleep(0.05) # 응답을 기다릴 경우 필요
        except serial.SerialException as e:
            logger.error(f"명령어 전송 중 오류 발생: {e}")
            self._initialize_serial() # 연결 재시도

    def release(self):
        """시리얼 포트 연결을 해제합니다."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"시리얼 포트 {self.port} 연결이 해제되었습니다.")
