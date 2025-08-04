import cv2
import numpy as np
from typing import Optional, Tuple, Generator
import time
from loguru import logger

class VideoStream:
    """다양한 비디오 소스를 처리하는 스트림 클래스"""

    def __init__(self, source=0, resolution=(1920, 1080), fps=30):
        """
        비디오 스트림을 초기화합니다.
        :param source: 카메라 인덱스 또는 비디오 파일 경로
        :param resolution: (width, height)
        :param fps: 초당 프레임
        """
        self.source = source
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        self.is_running = False
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """카메라를 초기화합니다."""
        try:
            logger.info(f"cv2.VideoCapture({self.source})를 시도합니다...")
            self.cap = cv2.VideoCapture(self.source)
            
            # --- 디버깅 로그 추가 ---
            if self.cap.isOpened():
                logger.success(f"카메라 {self.source}가 성공적으로 열렸습니다.")
            else:
                logger.error(f"카메라 {self.source}를 여는 데 실패했습니다. isOpened()가 False를 반환했습니다.")
                # 실패 시 더 이상 진행하지 않고 즉시 예외 발생
                raise RuntimeError(f"비디오 소스를 열 수 없습니다: {self.source}")

            # 카메라 설정
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화

            logger.info(f"카메라 초기화 완료: {self.source}, 해상도: {self.resolution}, FPS: {self.fps}")
                
        except Exception as e:
            logger.error(f"카메라 초기화 중 예외 발생: {e}")
            # self.cap이 None이거나 열리지 않았을 수 있으므로 release 호출 전 확인
            if self.cap:
                self.cap.release()
            raise

    def get_frame(self) -> Optional[np.ndarray]:
        """단일 프레임을 가져옵니다."""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("프레임을 읽을 수 없습니다.")
            return None
        
        return frame

    def get_frames(self) -> Generator[np.ndarray, None, None]:
        """프레임 생성하는 Generator 함수"""
        self.is_running = True
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.is_running and self.cap and self.cap.isOpened():
                frame = self.get_frame()
                if frame is not None:
                    frame_count += 1
                    
                    # FPS 계산 (1초마다)
                    if frame_count % self.fps == 0:
                        elapsed_time = time.time() - start_time
                        current_fps = frame_count / elapsed_time
                        logger.debug(f"현재 FPS: {current_fps:.2f}")
                    
                    yield frame
                else:
                    logger.warning("프레임을 가져올 수 없습니다.")
                    time.sleep(0.1)  # 잠시 대기
                    
        except Exception as e:
            logger.error(f"비디오 스트림 오류: {e}")
        finally:
            self.is_running = False

    def get_frame_with_timestamp(self) -> Optional[Tuple[np.ndarray, float]]:
        """타임스탬프와 함께 프레임을 가져옵니다."""
        frame = self.get_frame()
        if frame is not None:
            return frame, time.time()
        return None

    def set_resolution(self, width: int, height: int):
        """해상도를 변경합니다."""
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.resolution = (width, height)
            logger.info(f"해상도 변경: {self.resolution}")

    def get_camera_info(self) -> dict:
        """카메라 정보를 반환합니다."""
        if not self.cap or not self.cap.isOpened():
            return {}
        
        return {
            "source": self.source,
            "resolution": self.resolution,
            "fps": self.fps,
            "is_opened": self.cap.isOpened(),
            "frame_width": self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            "frame_height": self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            "actual_fps": self.cap.get(cv2.CAP_PROP_FPS)
        }

    def stop(self):
        """스트림을 중지합니다."""
        self.is_running = False

    def release(self):
        """비디오 캡처 객체를 해제합니다."""
        self.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info("비디오 캡처 객체 해제 완료")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

