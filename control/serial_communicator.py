import serial
import time
import asyncio
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
        """시리얼 포트 연결을 초기화하고 아두이노의 응답을 확인합니다."""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            logger.info(f"시리얼 포트 {self.port}에 {self.baud_rate}bps로 연결을 시도합니다...")
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=2) # 타임아웃 2초로 증가
            time.sleep(2)  # 아두이노가 리셋되고 메시지를 보낼 시간을 줍니다.

            # 연결 후 아두이노로부터 초기 메시지 읽기
            initial_message = self.serial.readline().decode(errors='ignore').strip()
            if initial_message:
                logger.success(f"아두이노 연결 성공. 응답: \"{initial_message}\"")
            else:
                logger.warning("포트 연결은 성공했으나, 아두이노로부터 응답이 없습니다.")

        except serial.SerialException as e:
            logger.error(f"시리얼 포트 {self.port}에 연결할 수 없습니다: {e}")
            logger.error("모의 모드로 전환합니다. 실제 하드웨어 제어가 이루어지지 않습니다.")
            self.mock_mode = True
            self.serial = None

        except serial.SerialException as e:
            logger.error(f"시리얼 포트 {self.port}에 연결할 수 없습니다: {e}")
            logger.error("모의 모드로 전환합니다. 실제 하드웨어 제어가 이루어지지 않습니다.")
            self.mock_mode = True
            self.serial = None

    async def send_command(self, command: str) -> str:
        """아두이노에 비동기적으로 명령어를 전송하고 응답을 받습니다."""
        if self.mock_mode:
            logger.info(f"[MOCK] 시리얼 명령어: {command} -> 응답: OK")
            return "OK"
        
        if not self.serial or not self.serial.is_open:
            logger.error("시리얼 포트가 열려있지 않습니다.")
            return "Error: Serial port not open."

        def sync_io():
            try:
                full_command = f"{command}\n"
                self.serial.write(full_command.encode('utf-8'))
                logger.debug(f"시리얼 명령어 전송 ->: {command}")
                
                # 아두이노로부터 응답을 읽습니다.
                response = self.serial.readline().decode('utf-8').strip()
                logger.debug(f"응답 수신 <-: {response}")
                return response
            except serial.SerialException as e:
                logger.error(f"시리얼 통신 중 에러 발생: {e}")
                return f"Error: {e}"

        try:
            return await asyncio.to_thread(sync_io)
        except Exception as e:
            logger.error(f"asyncio.to_thread 실행 중 에러: {e}")
            return f"Error: {e}"

    def release(self):
        """시리얼 포트 연결을 해제합니다."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"시리얼 포트 {self.port} 연결이 해제되었습니다.")
