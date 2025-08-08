
import cv2
import numpy as np
from typing import Dict, Any, List
from loguru import logger

from .person_detector import PersonDetector
from .pose_detector import PoseDetector
from .danger_zone_mapper import DangerZoneMapper

class Detector:
    """모든 하위 탐지 모듈을 총괄하고, 종합적인 탐지 결과를 반환하는 클래스."""

    def __init__(self, config: Dict[str, Any]):
        """
        Detector를 초기화하고 모든 하위 탐지기를 설정합니다.

        Args:
            config: 전체 탐지기 설정을 담은 딕셔너리
        """
        try:
            self.person_detector = PersonDetector(**config.get('person_detector', {}))
            # PoseDetector는 이제 pose_model 관련 설정을 받지 않습니다.
            self.pose_detector = PoseDetector(**config.get('fall_detector', {}))
            
            self.danger_zone_mapper = DangerZoneMapper()
            
            logger.info("Detector 및 모든 하위 탐지기 초기화 완료")
        except Exception as e:
            logger.error(f"Detector 초기화 중 심각한 오류 발생: {e}")
            raise

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        2단계 탐지 파이프라인:
        1. 가벼운 PersonDetector로 사람을 먼저 찾습니다.
        2. 사람이 감지된 경우에만 PoseDetector로 넘어짐 등 상세 분석을 수행합니다.
        """
        # 1. 사람 탐지 (항상 실행)
        detected_persons = self.person_detector.detect(frame)
        
        # 사람이 없으면 더 이상 분석할 필요가 없음
        if not detected_persons:
            return {
                "persons": [],
                "poses": [], # 호환성을 위해 유지
                "danger_zone_alerts": []
            }

        # 2. 자세 분석 (사람이 감지된 경우에만 실행)
        # person_detector의 결과를 pose_detector로 넘겨서 추가 분석을 요청합니다.
        # 이제 detected_persons 리스트에 pose_analysis 결과가 추가되어 반환됩니다.
        persons_with_pose_analysis = self.pose_detector.detect(frame, detected_persons)

        # 3. 위험 구역 침입 분석 (분석이 완료된 최종 결과 사용)
        danger_zone_alerts = self.danger_zone_mapper.check_all_zones(persons_with_pose_analysis)

        # 4. 최종 결과 종합
        detection_result = {
            # 이제 persons 키가 모든 정보를 담는 유일한 정보원이 됩니다.
            "persons": persons_with_pose_analysis,
            "poses": [], # 레거시 호환 또는 디버깅을 위해 빈 리스트로 유지
            "danger_zone_alerts": danger_zone_alerts
        }

        return detection_result

    def draw_detections(self, frame: np.ndarray, detection_result: Dict[str, Any]) -> np.ndarray:
        """
        모든 탐지 결과를 입력 프레임에 시각화합니다.
        """
        result_frame = frame.copy()
        
        # 1. 위험 구역 그리기 (침입 시 색상 변경)
        alerts = detection_result.get('danger_zone_alerts', [])
        result_frame = self.danger_zone_mapper.visualize_zones(result_frame, alerts)

        # 2. 최종 탐지 결과(사람 BBox + 넘어짐 분석) 그리기
        # 이제 PoseDetector의 draw_poses가 이 역할을 담당합니다.
        persons = detection_result.get('persons', [])
        result_frame = self.pose_detector.draw_poses(result_frame, persons)

        return result_frame
