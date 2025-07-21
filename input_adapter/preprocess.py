import cv2
import numpy as np
from typing import Tuple, Optional, Callable
from loguru import logger

class VideoPreprocessor:
    """비디오 프레임 전처리 클래스"""
    
    def __init__(self, target_size: Tuple[int, int] = (640, 640), 
                 normalize: bool = True, 
                 apply_noise_reduction: bool = True):
        """
        전처리기를 초기화합니다.
        :param target_size: 목표 이미지 크기 (width, height)
        :param normalize: 정규화 적용 여부
        :param apply_noise_reduction: 노이즈 감소 적용 여부
        """
        self.target_size = target_size
        self.normalize = normalize
        self.apply_noise_reduction = apply_noise_reduction
        
        # 노이즈 감소를 위한 커널
        self.noise_kernel = np.ones((3, 3), np.uint8)
        
        logger.info(f"전처리기 초기화: 크기={target_size}, 정규화={normalize}, 노이즈감소={apply_noise_reduction}")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        프레임을 전처리합니다.
        :param frame: 입력 프레임
        :return: 전처리된 프레임
        """
        if frame is None:
            logger.warning("입력 프레임이 None입니다.")
            return None
        
        try:
            # 1. 노이즈 감소
            if self.apply_noise_reduction:
                frame = self._reduce_noise(frame)
            
            # 2. 크기 조정
            frame = self._resize_frame(frame)
            
            # 3. 정규화
            if self.normalize:
                frame = self._normalize_frame(frame)
            
            return frame
            
        except Exception as e:
            logger.error(f"프레임 전처리 중 오류: {e}")
            return frame

    def _reduce_noise(self, frame: np.ndarray) -> np.ndarray:
        """노이즈를 감소시킵니다."""
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        return blurred

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """프레임 크기를 조정합니다."""
        return cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)

    def _normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """프레임을 정규화합니다."""
        if frame.dtype == np.uint8:
            return frame.astype(np.float32) / 255.0
        return frame

    def enhance_contrast(self, frame: np.ndarray) -> np.ndarray:
        """대비를 향상시킵니다."""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
        if len(frame.shape) == 3:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(frame)

    def apply_roi(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
        """
        관심 영역(ROI)을 적용합니다.
        :param frame: 입력 프레임
        :param roi: (x, y, width, height) 형태의 ROI
        :return: ROI가 적용된 프레임
        """
        x, y, w, h = roi
        return frame[y:y+h, x:x+w]

    def detect_motion(self, frame1: np.ndarray, frame2: np.ndarray, 
                     threshold: float = 25.0) -> Tuple[bool, np.ndarray]:
        """
        두 프레임 간의 움직임을 감지합니다.
        :param frame1: 이전 프레임
        :param frame2: 현재 프레임
        :param threshold: 움직임 감지 임계값
        :return: (움직임 감지 여부, 움직임 마스크)
        """
        if frame1 is None or frame2 is None:
            return False, None
        
        # 그레이스케일 변환
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
        
        # 프레임 차이 계산
        diff = cv2.absdiff(gray1, gray2)
        
        # 이진화
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        # 노이즈 제거
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # 움직임 감지
        motion_detected = bool(np.sum(thresh) > 1000)  # 임계값 조정 가능
        
        return motion_detected, thresh

    def get_frame_statistics(self, frame: np.ndarray) -> dict:
        """프레임 통계 정보를 반환합니다."""
        if frame is None:
            return {}
        
        stats = {
            "shape": frame.shape,
            "dtype": str(frame.dtype),
            "min_value": float(np.min(frame)),
            "max_value": float(np.max(frame)),
            "mean_value": float(np.mean(frame)),
            "std_value": float(np.std(frame))
        }
        
        return stats

    def create_processing_pipeline(self, steps: list) -> Callable:
        """
        전처리 파이프라인을 생성합니다.
        :param steps: 전처리 단계 리스트
        :return: 파이프라인 함수
        """
        def pipeline(frame):
            result = frame
            for step in steps:
                if hasattr(self, step):
                    result = getattr(self, step)(result)
                else:
                    logger.warning(f"알 수 없는 전처리 단계: {step}")
            return result
        
        return pipeline