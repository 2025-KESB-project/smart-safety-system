import numpy as np
from typing import List, Dict, Any
from ultralytics import YOLO
from loguru import logger
import torch

class PersonDetector:
    """사람 감지 (YOLOv8 사용, 핵심 기능만)"""

    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.3):
        """
        사람 감지기 초기화

        Args:
            model_path: YOLO 모델 경로
            conf_threshold: 신뢰도 임계값
        """
        try:
            # 1. 하드웨어 장치 자동 감지 (CUDA > MPS > CPU 순)
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.success("PersonDetector: NVIDIA GPU (CUDA)를 감지하여 사용합니다.")
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
                logger.success("PersonDetector: Apple Silicon GPU (MPS)를 감지하여 사용합니다.")
            else:
                self.device = torch.device("cpu")
                logger.warning("PersonDetector: 사용 가능한 GPU가 없어 CPU를 사용합니다.")

            self.model = YOLO(model_path)
            self.model.to(self.device) # 모델을 지정된 장치로 이동
            self.conf_threshold = conf_threshold
            
            # 'person' 클래스 ID를 모델로부터 동적으로 찾아오도록 개선
            self.person_class_id = self._get_class_id('person')
            if self.person_class_id is None:
                raise ValueError(f"모델 '{model_path}'에서 'person' 클래스를 찾을 수 없습니다.")

            logger.info(f"PersonDetector 초기화 완료: {model_path}, 임계값: {conf_threshold}")
            logger.info(f"'person' 클래스 ID는 {self.person_class_id} 입니다.")

        except Exception as e:
            logger.error(f"PersonDetector 초기화 실패: {e}")
            raise

    def _get_class_id(self, class_name: str) -> int | None:
        """모델의 클래스 이름 목록에서 특정 클래스의 ID를 찾아 반환합니다."""
        try:
            for class_id, name in self.model.names.items():
                if name.lower() == class_name.lower():
                    return class_id
            return None
        except Exception as e:
            logger.error(f"클래스 ID를 찾는 중 오류 발생: {e}")
            return None

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        프레임에서 사람을 감지합니다. 오류 발생 시 빈 리스트를 반환하여 시스템 안정성을 확보합니다.

        Args:
            frame: BGR 이미지 (numpy.ndarray)

        Returns:
            감지된 사람 리스트 [{"bbox": [x1, y1, x2, y2], "confidence": conf}, ...]
        """
        if self.person_class_id is None:
            logger.warning("'person' 클래스가 정의되지 않아 감지를 건너뜁니다.")
            return []

        try:
            # 예측 시에도 장치 지정
            results = self.model.predict(source=frame, conf=self.conf_threshold, classes=[self.person_class_id], device=self.device, verbose=False)
            
            persons = []
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    conf = float(box.conf[0].item())
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    persons.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf
                    })
            return persons

        except Exception as e:
            logger.error(f"사람 감지 중 예측 오류 발생: {e}")
            # 오류 발생 시 빈 리스트를 반환하여 시스템이 중단되는 것을 방지
            return []
