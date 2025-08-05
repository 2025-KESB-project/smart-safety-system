import serial
import time
import threading
from loguru import logger
from typing import Optional

class SerialCommunicator:
    """
    아두이노와의 시리얼 통신을 전담하며, 스레드 안전성을 보장하는 클래스.
    """

    def __init__(self, port: str, baud_rate: int, mock_mode: bool = True):
        self.port = port
        self.baud_rate = baud_rate
        self.mock_mode = mock_mode
        self.serial: Optional[serial.Serial] = None
        self.lock = threading.Lock()  # 스레드 동기화를 위한 Lock 객체

        if not self.mock_mode:
            self._initialize_serial()

    def _initialize_serial(self):
        """시리얼 포트 연결을 초기화합니다."""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            logger.info(f"시리얼 포트 {self.port}에 {self.baud_rate}bps로 연결을 시도합니다...")
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)

            initial_message = self.serial.readline().decode(errors='ignore').strip()
            if initial_message:
                logger.success(f"아두이노 연결 성공. 응답: \"{initial_message}\"")
            else:
                logger.warning("포트 연결은 성공했으나, 아두이노로부터 응답이 없습니다.")

        except serial.SerialException as e:
            logger.error(f"시리얼 포트 {self.port}에 연결할 수 없습니다: {e}")
            self.mock_mode = True
            self.serial = None

    def send_command(self, command: str):
        """스레드 안전하게 아두이노에 명령어를 전송합니다."""
        if self.mock_mode or not self.serial or not self.serial.is_open:
            logger.info(f"[MOCK] 시리얼 명령어 전송: {command}")
            return

        with self.lock:  # Lock을 사용하여 동시 접근을 막습니다.
            try:
                full_command = f"{command}\n"
                self.serial.write(full_command.encode('utf-8'))
                logger.debug(f"시리얼 명령어 전송: {command}")
            except serial.SerialException as e:
                logger.error(f"명령어 전송 중 오류 발생: {e}")
                self._initialize_serial()

    def read_line(self) -> Optional[str]:
        """스레드 안전하게 아두이노로부터 한 줄의 데이터를 읽어 반환합니다."""
        if self.mock_mode or not self.serial or not self.serial.is_open:
            return None

        with self.lock:  # Lock을 사용하여 동시 접근을 막습니다.
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        logger.success(f"[SerialIO] 데이터 수신: {line}")
                        return line
            except serial.SerialException as e:
                logger.error(f"데이터 수신 중 오류 발생: {e}")
                self._initialize_serial()
        return None

    def close(self):
        """시리얼 포트 연결을 해제합니다."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"시리얼 포트 {self.port} 연결이 해제되었습니다.")
