import cv2
import numpy as np
from typing import List, Dict, Any
from ultralytics import YOLO
from loguru import logger
import torch

class PoseDetector:
    """
    yolov8n-pose.pt와 fall_det_1.pt 모델을 함께 사용하여 사람의 자세를 분석하고,
    두 모델의 결과를 AND 조건으로 결합하여 넘어짐 상태를 정밀하게 탐지합니다.
    """

    def __init__(self, pose_model_path: str, fall_model_path: str, conf_threshold=0.5):
        """
        자세 탐지기 초기화. 2개의 모델을 로드합니다.
        1. self.pose_model: 사람의 관절과 바운딩 박스 탐지용
        2. self.fall_model: 'Fall-Detected' 클래스 탐지용
        """
        try:
            self.pose_model = YOLO(pose_model_path)
            self.fall_model = YOLO(fall_model_path)
            self.conf_threshold = conf_threshold
            logger.info(f"PoseDetector 초기화 완료: pose_model({pose_model_path}), fall_model({fall_model_path}) 로드 완료")
        except Exception as e:
            logger.error(f"PoseDetector 초기화 중 모델 로드 실패: {e}")
            raise

    def _calculate_iou(self, boxA: np.ndarray, boxB: np.ndarray) -> float:
        """두 바운딩 박스 간의 Intersection over Union (IoU)을 계산합니다."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        
        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        프레임에서 모든 사람의 자세를 탐지하고, 두 모델의 결과를 종합하여 넘어짐을 분석합니다.
        """
        try:
            # 1. 자세 모델 실행
            pose_results = self.pose_model.predict(source=frame, conf=self.conf_threshold, verbose=False)
            # 2. 넘어짐 감지 모델 실행 (신뢰도 임계값 0.4 적용)
            fall_results = self.fall_model.predict(source=frame, conf=0.4, verbose=False)
        except Exception as e:
            logger.error(f"모델 예측 중 오류 발생: {e}")
            return []

        # 넘어짐 모델에서 'Fall-Detected'로 감지된 바운딩 박스 목록 추출
        fall_bboxes = []
        if fall_results and fall_results[0].boxes:
            for box in fall_results[0].boxes:
                if self.fall_model.names[int(box.cls)] == 'Fall-Detected':
                    fall_bboxes.append(box.xyxy[0].cpu().numpy().astype(int))

        detected_poses = []
        if not pose_results or pose_results[0].keypoints is None:
            return []

        for i, person_keypoints in enumerate(pose_results[0].keypoints):
            bbox = pose_results[0].boxes[i].xyxy[0].cpu().numpy().astype(int)
            keypoints = person_keypoints.xy[0].cpu().numpy()
            keypoints_conf = person_keypoints.conf[0].cpu().numpy()
            
            keypoints_map = {name: (kp, conf) for name, (kp, conf) in zip(self.pose_model.names.values(), zip(keypoints, keypoints_conf))}

            # 자세 분석 (넘어짐 감지 결과 포함)
            analysis = self._analyze_pose(bbox, keypoints_map, fall_bboxes)

            detected_poses.append({
                "person_id": i,
                "bbox": bbox.tolist(),
                "keypoints": {name: kp.tolist() for name, (kp, conf) in keypoints_map.items() if conf > 0.3}, # 임계값 0.4 -> 0.3
                "analysis": analysis
            })
        
        return detected_poses

    def _analyze_pose(self, bbox: np.ndarray, keypoints: Dict[str, Any], fall_bboxes: List[np.ndarray]) -> Dict[str, Any]:
        """
        단일 사람의 자세를 분석합니다.
        넘어짐 모델을 필수 조건으로, [몸통 수평 OR BBox 비율]을 선택 조건으로 결합합니다.
        """
        analysis = {
            'is_falling': False,
            'is_crouching': False,
            'risk_level': 'low',
            'description': 'Normal'
        }

        x1, y1, x2, y2 = bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1

        # --- 넘어짐 탐지 (Flexible OR-Condition Logic) ---

        # 조건 1 (필수): 넘어짐 감지 모델이 이 사람을 탐지했는가?
        is_model_falling = False
        for fall_box in fall_bboxes:
            if self._calculate_iou(bbox, fall_box) > 0.5:
                is_model_falling = True
                break
        
        # 필수 조건(is_model_falling)이 충족되었을 때만 추가 분석 수행
        if is_model_falling:
            # 조건 2-a (선택): 몸통이 수평에 가까운가?
            is_torso_horizontal = False
            try:
                l_shoulder, l_shoulder_conf = keypoints['left_shoulder']
                r_shoulder, r_shoulder_conf = keypoints['right_shoulder']
                l_hip, l_hip_conf = keypoints['left_hip']
                r_hip, r_hip_conf = keypoints['right_hip']

                if all(conf > 0.5 for conf in [l_shoulder_conf, r_shoulder_conf, l_hip_conf, r_hip_conf]):
                    shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2
                    hip_y = (l_hip[1] + r_hip[1]) / 2
                    torso_vertical_dist = abs(hip_y - shoulder_y)

                    if torso_vertical_dist < bbox_height * 0.05:
                        is_torso_horizontal = True
            except (KeyError, ZeroDivisionError):
                pass

            # 조건 2-b (선택): 바운딩 박스의 너비가 높이보다 1.4배 이상인가?
            is_ratio_falling = bbox_width > bbox_height * 1.4

            # 최종 판정: 모델이 탐지했고, (몸통이 수평이거나 또는 BBox 비율이 맞을 때)
            if is_torso_horizontal or is_ratio_falling:
                analysis.update({
                    'is_falling': True,
                    'risk_level': 'critical',
                    'description': 'Falling Detected (Verified by Pose/BBox)'
                })
                return analysis # 넘어짐 확정 시 분석 종료

        # --- 끼임 / 웅크림 탐지 (넘어짐이 아닐 경우에만 수행) ---
        try:
            # (위에서 이미 계산된 값 재사용 또는 재계산)
            if 'l_shoulder' in locals() and 'l_hip' in locals(): # 관절 정보가 있을 경우
                shoulder_y = (keypoints['left_shoulder'][0][1] + keypoints['right_shoulder'][0][1]) / 2
                hip_y = (keypoints['left_hip'][0][1] + keypoints['right_hip'][0][1]) / 2
                torso_height = abs(hip_y - shoulder_y)

                if torso_height < bbox_height * 0.3:
                    analysis.update({
                        'is_crouching': True,
                        'risk_level': 'high',
                        'description': 'Abnormal Crouching / Stuck Detected'
                    })
        except (KeyError, ZeroDivisionError):
            pass
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

            cv2.rectangle(result_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            label = f"Risk: {analysis['description']}"
            cv2.putText(result_frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # 관절 그리기
            for name, kp in keypoints.items():
                cv2.circle(result_frame, (int(kp[0]), int(kp[1])), 3, color, -1)

        return result_frame
