
import cv2
import numpy as np
from typing import Dict, Any, List
from loguru import logger

from .person_detector import PersonDetector
from .pose_detector import PoseDetector
from .danger_zone_mapper import DangerZoneMapper
from server.services.zone_service import ZoneService

class Detector:
    """모든 하위 탐지 모듈을 총괄하고, 종합적인 탐지 결과를 반환하는 클래스."""

    def __init__(self, config: Dict[str, Any], zone_service: ZoneService):
        """
        Detector를 초기화하고 모든 하위 탐지기를 설정합니다.
        ZoneService는 외부(app.py)에서 주입받아 DangerZoneMapper에 전달합니다.

        Args:
            config: 전체 탐지기 설정을 담은 딕셔너리
            zone_service: 초기화된 ZoneService 인스턴스
        """
        try:
            self.person_detector = PersonDetector(**config.get('person_detector', {}))
            self.pose_detector = PoseDetector(**config.get('pose_detector', {}))
            
            # 주입받은 ZoneService를 사용하여 DangerZoneMapper 초기화
            self.danger_zone_mapper = DangerZoneMapper(zone_service=zone_service)
            
            logger.info("Detector 및 모든 하위 탐지기 초기화 완료")
        except Exception as e:
            logger.error(f"Detector 초기화 중 심각한 오류 발생: {e}")
            raise

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        주어진 프레임에서 모든 탐지 및 분석을 순차적으로 수행합니다.

        Args:
            frame: 분석할 BGR 이미지 프레임 (numpy.ndarray)

        Returns:
            모든 탐지 결과를 종합한 딕셔너리
        """
        # 1. 사람 탐지 (가장 기본)
        detected_persons = self.person_detector.detect(frame)
        if not detected_persons:
            # 사람이 없으면 더 이상 분석할 필요가 없음
            return {
                "persons": [],
                "poses": [],
                "danger_zone_alerts": []
            }

        # 2. 자세 분석
        # PersonDetector의 bbox를 PoseDetector에 직접 전달할 수도 있지만,
        # PoseDetector가 자체적으로 사람을 찾는 것이 더 정확할 수 있음.
        detected_poses = self.pose_detector.detect(frame)

        # 3. 위험 구역 침입 분석
        # PersonDetector가 찾은 bbox를 기준으로 침입 여부 판단
        danger_zone_alerts = self.danger_zone_mapper.check_all_zones(detected_persons)

        # 4. 최종 결과 종합
        detection_result = {
            "persons": detected_persons,
            "poses": detected_poses,
            "danger_zone_alerts": danger_zone_alerts
        }

        return detection_result

    def draw_detections(self, frame: np.ndarray, detection_result: Dict[str, Any]) -> np.ndarray:
        """
        모든 탐지 결과를 입력 프레임에 시각화합니다.

        Args:
            frame: 원본 BGR 이미지 프레임
            detection_result: detect() 메소드의 반환값

        Returns:
            모든 시각화가 적용된 최종 프레임
        """
        result_frame = frame.copy()
        
        # 1. 위험 구역 그리기 (침입 시 색상 변경)
        alerts = detection_result.get('danger_zone_alerts', [])
        result_frame = self.danger_zone_mapper.visualize_zones(result_frame, alerts)

        # 2. 자세 정보 그리기 (BBox, 관절, 위험도)
        poses = detection_result.get('poses', [])
        result_frame = self.pose_detector.draw_poses(result_frame, poses)

        # 만약 PoseDetector가 그린 BBox 외에 PersonDetector의 BBox도 별도로 보고 싶다면 아래 주석 해제
        # for person in detection_result.get('persons', []):
        #     p_bbox = person['bbox']
        #     cv2.rectangle(result_frame, (p_bbox[0], p_bbox[1]), (p_bbox[2], p_bbox[3]), (255, 255, 255), 1) # 흰색 점선

        return result_frame
