import serial
import time
import threading
import json
from loguru import logger
from typing import Optional, Callable


class SerialCommunicator:
    """
    아두이노와의 시리얼 통신을 전담하며, 스레드 안전성을 보장하는 클래스.
    백그라운드 리스너 스레드를 통해 하드웨어의 비동기 신호를 감지합니다.
    """

    def __init__(self, port: str, baud_rate: int, mock_mode: bool = True):
        self.port = port
        self.baud_rate = baud_rate
        self.mock_mode = mock_mode
        self.serial: Optional[serial.Serial] = None
        self.lock = threading.Lock()  # 스레드 동기화를 위한 Lock 객체
        self.is_listening = False
        self.listener_thread: Optional[threading.Thread] = None
        self.lock_system_callback: Optional[Callable[[str], None]] = None
        self.is_locked_checker: Optional[Callable[[], bool]] = None

        if not self.mock_mode:
            self._initialize_serial()

    def _initialize_serial(self):
        """시리얼 포트 연결을 초기화합니다."""
        with self.lock:
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

    def set_lock_system_callback(self, callback: Callable[[str], None]):
        """비상 정지 시 호출될 콜백 함수를 설정합니다."""
        self.lock_system_callback = callback
        logger.info("시스템 잠금 콜백 함수가 SerialCommunicator에 설정되었습니다.")

    def set_is_locked_checker(self, checker: Callable[[], bool]):
        """시스템 잠금 상태를 확인할 콜백 함수를 설정합니다."""
        self.is_locked_checker = checker
        logger.info("시스템 잠금 상태 확인 콜백이 SerialCommunicator에 설정되었습니다.")

    def _listening_loop(self):
        """리스너 스레드에서 실행될 메인 루프."""
        logger.info("아두이노 시리얼 리스너 스레드를 시작합니다...")
        while self.is_listening:
            line = self.read_line()
            if line:
                # 수신된 데이터가 JSON 형태일 가능성이 있을 때만 파싱 시도
                if line.strip().startswith('{'):
                    logger.debug(f"리스너가 JSON으로 추정되는 신호 수신: {line}")
                    try:
                        data = json.loads(line)
                        # 하드웨어가 자율적으로 전원을 끈 경우를 비상 상황으로 간주
                        if data.get("type") == "STATUS" and data.get("source") == "AUTO" and data.get("power") == "OFF":
                            # 시스템이 아직 잠겨있지 않을 때만 잠금 로직을 실행
                            if self.is_locked_checker and not self.is_locked_checker():
                                logger.critical("하드웨어 자율 전원 차단 신호 감지! (비상 정지로 간주)")
                                if self.lock_system_callback:
                                    self.lock_system_callback("Hardware auto power-off detected")
                            else:
                                logger.debug("이미 시스템이 잠겨있으므로 중복된 하드웨어 전원 차단 신호는 무시합니다.")

                    except json.JSONDecodeError:
                        # JSON 파싱 실패는 자주 있을 수 있으므로 debug 레벨로 로깅
                        logger.debug(f"수신된 데이터가 JSON 형식이 아닙니다: {line}")
                else:
                    # JSON 형태가 아닌 데이터는 일반 명령어 응답으로 간주하고 무시
                    logger.debug(f"리스너가 일반 텍스트 응답 수신 (무시): {line}")

            time.sleep(0.1) # CPU 사용량 조절
        logger.info("시리얼 리스너 스레드를 종료합니다.")

    def start_listening(self):
        """백그라운드에서 시리얼 입력을 감지하는 스레드를 시작합니다."""
        if self.mock_mode:
            logger.info("[MOCK] 시리얼 리스너는 모의 모드에서 실행되지 않습니다.")
            return
        
        if not self.is_listening:
            self.is_listening = True
            self.listener_thread = threading.Thread(target=self._listening_loop, daemon=True)
            self.listener_thread.start()

    def send_command(self, command: str):
        """스레드 안전하게 아두이노에 명령어를 전송합니다."""
        if self.mock_mode or not self.serial or not self.serial.is_open:
            logger.info(f"[MOCK] 시리얼 명령어 전송: {command}")
            return

        with self.lock:
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

        with self.lock:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        return line
            except serial.SerialException as e:
                logger.error(f"데이터 수신 중 오류 발생: {e}")
                self._initialize_serial()
        return None

    def close(self):
        """시리얼 포트 연결을 해제하고 리스너 스레드를 중지합니다."""
        logger.info("SerialCommunicator를 종료합니다...")
        self.is_listening = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join()

        if self.serial and self.serial.is_open:
            with self.lock:
                self.serial.close()
            logger.info(f"시리얼 포트 {self.port} 연결이 해제되었습니다.")
