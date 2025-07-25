import cv2
import numpy as np
from typing import List, Dict, Any
from ultralytics import YOLO
from loguru import logger
import torch

class PoseDetector:
    """YOLOv8-pose 모델을 사용하여 사람의 자세를 분석하고 비정상 상태(넘어짐, 낌)를 탐지합니다."""

    def __init__(self, model_path='yolov8n-pose.pt', conf_threshold=0.5):
        """
        자세 탐지기 초기화

        Args:
            model_path: YOLOv8 Pose 모델 경로
            conf_threshold: 사람 객체 탐지에 대한 신뢰도 임계값
        """
        try:
            # 알려진 MPS 버그로 인해 Pose 모델은 CPU를 사용하도록 강제합니다.
            self.device = "cpu"
            logger.warning("PoseDetector는 알려진 MPS 버그를 피하기 위해 'cpu' 장치를 사용합니다.")

            self.model = YOLO(model_path)
            self.model.to(self.device) # 모델을 CPU로 이동
            self.conf_threshold = conf_threshold
            
            # --- Keypoint 이름 처리 로직 개선 ---
            # 초기화 시점에 단 한번만 확인하여, 매번 경고가 발생하는 것을 방지합니다.
            self.kpt_names = None
            # 모델의 names 속성이 있고, 그 안에 17개의 COCO keypoint 이름이 있는지 확인
            if hasattr(self.model, 'names') and isinstance(self.model.names, dict) and len(self.model.names) == 17:
                self.kpt_names = self.model.names
                logger.info("PoseDetector가 모델에서 17개의 Keypoint 이름을 성공적으로 로드했습니다.")
            else:
                logger.warning(
                    f"모델의 'names' 속성에서 17개의 Keypoint 이름을 찾을 수 없습니다. "
                    f"(Found: {getattr(self.model, 'names', 'N/A')}). "
                    "감지 시 일반 이름(kp_0, kp_1...)을 사용합니다."
                )
            
            logger.info(f"PoseDetector 초기화 완료: {model_path}")
        except Exception as e:
            logger.error(f"PoseDetector 초기화 실패: {e}")
            raise

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        프레임에서 모든 사람의 자세를 탐지하고 분석합니다.

        Args:
            frame: BGR 이미지 (numpy.ndarray)

        Returns:
            분석된 자세 정보 리스트. 각 요소는 한 사람에 대한 정보를 담은 딕셔너리.
            e.g., [{"bbox": [...], "keypoints": {...}, "analysis": {...}}]
        """
        try:
            # 예측 시에도 장치를 명시적으로 CPU로 지정합니다.
            results = self.model.predict(source=frame, conf=self.conf_threshold, device=self.device, verbose=False)
        except Exception as e:
            logger.error(f"자세 예측 중 오류 발생: {e}")
            return []

        detected_poses = []
        
        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            return []

        if results[0].keypoints is None or len(results[0].keypoints) == 0:
            return []

        for i, person_keypoints in enumerate(results[0].keypoints):
            if i >= len(results[0].boxes):
                continue

            bbox = results[0].boxes[i].xyxy[0].cpu().numpy().astype(int)
            keypoints = person_keypoints.xy[0].cpu().numpy()
            keypoints_conf = person_keypoints.conf[0].cpu().numpy()

            # 관절 좌표를 이름과 매핑 (초기화 시 설정된 kpt_names 사용)
            keypoints_map = {}
            if self.kpt_names:
                for kp_idx, name in self.kpt_names.items():
                    if kp_idx < len(keypoints):
                        keypoints_map[name] = (keypoints[kp_idx], keypoints_conf[kp_idx])
            else:
                # kpt_names가 없으면 일반 이름 사용 (경고는 초기화 시 한번만)
                for kp_idx in range(len(keypoints)):
                    keypoints_map[f"kp_{kp_idx}"] = (keypoints[kp_idx], keypoints_conf[kp_idx])

            # 자세 분석
            analysis = self._analyze_pose(bbox, keypoints_map)

            detected_poses.append({
                "person_id": i,
                "bbox": bbox.tolist(),
                "keypoints": {name: kp.tolist() for name, (kp, conf) in keypoints_map.items() if conf > 0.4},
                "analysis": analysis
            })
        
        return detected_poses

    def _analyze_pose(self, bbox: np.ndarray, keypoints: Dict[str, Any]) -> Dict[str, Any]:
        """단일 사람의 관절 데이터를 기반으로 자세의 비정상 여부를 분석합니다."""
        analysis = {
            'is_falling': False,
            'is_crouching': False,
            'risk_level': 'low',
            'description': 'Normal'
        }

        x1, y1, x2, y2 = bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1

        # --- 넘어짐 판단 로직 (요청사항 반영하여 개선) ---

        # 규칙 1: 바운딩 박스의 가로/세로 비율
        is_fallen_by_bbox = bbox_width > bbox_height * 1.2

        # 규칙 2: 주요 관절의 수직 위치 분석
        is_fallen_by_keypoints = False
        try:
            # 머리, 어깨, 엉덩이 관절의 좌표와 신뢰도 추출
            nose, nose_conf = keypoints.get('nose', ([0, 0], 0))
            l_shoulder, l_shoulder_conf = keypoints.get('left_shoulder', ([0, 0], 0))
            r_shoulder, r_shoulder_conf = keypoints.get('right_shoulder', ([0, 0], 0))
            l_hip, l_hip_conf = keypoints.get('left_hip', ([0, 0], 0))
            r_hip, r_hip_conf = keypoints.get('right_hip', ([0, 0], 0))

            # 어깨와 엉덩이의 평균 y좌표 계산 (보이는 관절만 사용)
            visible_shoulders_y = [p[1] for p, c in [(l_shoulder, l_shoulder_conf), (r_shoulder, r_shoulder_conf)] if c > 0.5]
            visible_hips_y = [p[1] for p, c in [(l_hip, l_hip_conf), (r_hip, r_hip_conf)] if c > 0.5]

            if visible_shoulders_y and visible_hips_y:
                avg_shoulder_y = sum(visible_shoulders_y) / len(visible_shoulders_y)
                avg_hip_y = sum(visible_hips_y) / len(visible_hips_y)

                # 어깨가 엉덩이보다 아래에 있으면 넘어진 것으로 판단
                if avg_shoulder_y > avg_hip_y:
                    is_fallen_by_keypoints = True
            
            # 머리가 엉덩이보다 아래에 있는 경우도 추가
            elif nose_conf > 0.5 and visible_hips_y:
                avg_hip_y = sum(visible_hips_y) / len(visible_hips_y)
                if nose[1] > avg_hip_y:
                    is_fallen_by_keypoints = True

        except Exception as e:
            logger.warning(f"넘어짐 관절 분석 중 오류: {e}")


        # 최종 넘어짐 판단: 두 규칙을 모두 만족해야 넘어진 것으로 간주
        if is_fallen_by_bbox and is_fallen_by_keypoints:
            analysis.update({
                'is_falling': True,
                'risk_level': 'critical',
                'description': 'Falling Detected'
            })
            # 넘어짐이 감지되면 가장 위험하므로 추가 분석 중단하고 즉시 반환
            return analysis

        # --- 끼임 / 웅크림 탐지 로직 (기존 로직 유지) ---
        try:
            l_shoulder, l_shoulder_conf = keypoints.get('left_shoulder', ([0, 0], 0))
            r_shoulder, r_shoulder_conf = keypoints.get('right_shoulder', ([0, 0], 0))
            l_hip, l_hip_conf = keypoints.get('left_hip', ([0, 0], 0))
            r_hip, r_hip_conf = keypoints.get('right_hip', ([0, 0], 0))

            if all(c > 0.6 for c in [l_shoulder_conf, r_shoulder_conf, l_hip_conf, r_hip_conf]):
                shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2
                hip_y = (l_hip[1] + r_hip[1]) / 2
                torso_height = abs(hip_y - shoulder_y)

                if torso_height < bbox_height * 0.3:
                    analysis.update({
                        'is_crouching': True,
                        'risk_level': 'high',
                        'description': 'Abnormal Crouching / Stuck Detected'
                    })
        except Exception as e:
            logger.warning(f"웅크림 자세 분석 중 오류: {e}")

        return analysis

    def draw_poses(self, frame: np.ndarray, detected_poses: List[Dict[str, Any]]) -> np.ndarray:
        """
        탐지된 자세 정보(관절, BBox, 분석 결과)를 프레임에 시각화합니다.
        """
        result_frame = frame.copy()
        for pose in detected_poses:
            bbox = pose['bbox']
            analysis = pose['analysis']
            keypoints = pose['keypoints']

            color = (0, 255, 0) # 기본 초록색
            if analysis['risk_level'] == 'high':
                color = (0, 165, 255) # 주황색
            elif analysis['risk_level'] == 'critical':
                color = (0, 0, 255) # 빨간색

            # BBox 그리기
            cv2.rectangle(result_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

            # 분석 결과 텍스트 표시
            label = f"Risk: {analysis['description']}"
            cv2.putText(result_frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # 관절 그리기
            for name, kp in keypoints.items():
                cv2.circle(result_frame, (int(kp[0]), int(kp[1])), 3, color, -1)

        return result_frame