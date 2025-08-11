import cv2
import numpy as np
from typing import List, Dict, Any
from ultralytics import YOLO
from loguru import logger
import torch

class PoseDetector:
    """
    fall_det_1.pt 모델을 사용하여 넘어짐 상태를 탐지합니다.
    PersonDetector로부터 받은 사람 BBox 정보를 활용하여 연산을 최적화합니다.
    """

    def __init__(self, fall_model_path='fall_det_1.pt', conf_threshold=0.4):
        """
        자세 탐지기 초기화. fall_det_1.pt 모델만 로드합니다.
        """
        try:
            # 1. 하드웨어 장치 자동 감지 (CUDA > MPS > CPU 순)
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.success("PoseDetector: NVIDIA GPU (CUDA)를 감지하여 사용합니다.")
            # elif torch.backends.mps.is_available():
            #     self.device = torch.device("mps")
            #     logger.success("PoseDetector: Apple Silicon GPU (MPS)를 감지하여 사용합니다.")
            else:
                self.device = torch.device("cpu")
                logger.warning("PoseDetector: 사용 가능한 GPU가 없어 CPU를 사용합니다.")
            
            self.fall_model = YOLO(fall_model_path)
            self.fall_model.to(self.device)
            self.conf_threshold = conf_threshold
            logger.info(f"PoseDetector 초기화 완료: fall_model({fall_model_path}) 로드 완료")
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
        
        # ZeroDivisionError 방지
        denominator = float(boxAArea + boxBArea - interArea)
        if denominator == 0:
            return 0.0
            
        iou = interArea / denominator
        return iou

    def detect(self, frame: np.ndarray, detected_persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        미리 감지된 사람(detected_persons)을 대상으로 넘어짐을 분석합니다.
        """
        # 사람이 없으면 분석할 필요 없음
        if not detected_persons:
            return []
            
        try:
            # 1. 넘어짐 감지 모델 실행
            fall_results = self.fall_model.predict(source=frame, conf=self.conf_threshold, device=self.device, verbose=False)
        except Exception as e:
            logger.error(f"넘어짐 감지 모델 예측 중 오류 발생: {e}")
            return detected_persons # 오류 발생 시 원본 반환

        # 2. 넘어짐 모델에서 'Fall-Detected'로 감지된 바운딩 박스 목록 추출
        fall_bboxes = []
        if fall_results and fall_results[0].boxes:
            for box in fall_results[0].boxes:
                # 모델의 클래스 이름 목록에서 'Fall-Detected'를 찾아 ID를 비교
                if self.fall_model.names[int(box.cls)] == 'Fall-Detected':
                    fall_bboxes.append(box.xyxy[0].cpu().numpy().astype(int))

        # 3. 각 사람에 대해 넘어짐 분석 수행
        for person in detected_persons:
            person_bbox = np.array(person['bbox'])
            analysis = self._analyze_pose(person_bbox, fall_bboxes)
            # person 딕셔너리에 분석 결과 추가
            person['pose_analysis'] = analysis
        
        return detected_persons

    def _analyze_pose(self, person_bbox: np.ndarray, fall_bboxes: List[np.ndarray]) -> Dict[str, Any]:
        """
        단일 사람의 자세를 분석합니다. BBox 비율과 넘어짐 모델 결과를 결합합니다.
        """
        analysis = {
            'is_falling': False,
            'is_crouching': False, # 웅크림 탐지 로직은 관절 정보가 없어 제거됨
            'risk_level': 'low',
            'description': 'Normal'
        }

        x1, y1, x2, y2 = person_bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1
        
        # bbox_height가 0인 경우 ZeroDivisionError 방지
        if bbox_height == 0:
            return analysis

        # --- 넘어짐 탐지 ---

        # 조건 1 (필수): 넘어짐 감지 모델이 이 사람을 탐지했는가?
        is_model_falling = False
        for fall_box in fall_bboxes:
            if self._calculate_iou(person_bbox, fall_box) > 0.5:
                is_model_falling = True
                break
        
        # 필수 조건(is_model_falling)이 충족되었을 때만 추가 분석 수행
        if is_model_falling:
            # 조건 2 (선택): 바운딩 박스의 너비가 높이보다 1.4배 이상인가?
            is_ratio_falling = bbox_width > bbox_height * 1.4

            if is_ratio_falling:
                analysis.update({
                    'is_falling': True,
                    'risk_level': 'critical',
                    'description': 'Falling Detected (Verified by BBox Ratio)'
                })

        return analysis

    def draw_poses(self, frame: np.ndarray, detected_persons: List[Dict[str, Any]]) -> np.ndarray:
        """
        탐지된 사람의 BBox와 분석 결과를 프레임에 시각화합니다.
        """
        result_frame = frame.copy()
        if not detected_persons:
            return result_frame
        
        for person in detected_persons:
            bbox = person.get('bbox')
            # pose_analysis가 없는 경우를 대비하여 기본값 사용
            analysis = person.get('pose_analysis', {'risk_level': 'low', 'description': 'N/A'})

            if not bbox:
                continue

            color = (0, 255, 0) # 기본 초록색
            if analysis.get('risk_level') == 'high':
                color = (0, 165, 255) # 주황색
            elif analysis.get('risk_level') == 'critical':
                color = (0, 0, 255) # 빨간색

            cv2.rectangle(result_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            label = f"Risk: {analysis.get('description', 'N/A')}"
            cv2.putText(result_frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return result_frame
    #         except (KeyError, ZeroDivisionError):
    #             pass
    #
    #         # 조건 2-b (선택): 바운딩 박스의 너비가 높이보다 1.4배 이상인가?
    #         is_ratio_falling = bbox_width > bbox_height * 1.4
    #
    #         # 최종 판정: 모델이 탐지했고, (몸통이 수평이거나 또는 BBox 비율이 맞을 때)
    #         if is_torso_horizontal or is_ratio_falling:
    #             analysis.update({
    #                 'is_falling': True,
    #                 'risk_level': 'critical',
    #                 'description': 'Falling Detected (Verified by Pose/BBox)'
    #             })
    #             return analysis # 넘어짐 확정 시 분석 종료
    #
    #     # --- 끼임 / 웅크림 탐지 (넘어짐이 아닐 경우에만 수행) ---
    #     try:
    #         # (위에서 이미 계산된 값 재사용 또는 재계산)
    #         if 'l_shoulder' in locals() and 'l_hip' in locals(): # 관절 정보가 있을 경우
    #             shoulder_y = (keypoints['left_shoulder'][0][1] + keypoints['right_shoulder'][0][1]) / 2
    #             hip_y = (keypoints['left_hip'][0][1] + keypoints['right_hip'][0][1]) / 2
    #             torso_height = abs(hip_y - shoulder_y)
    #
    #             if torso_height < bbox_height * 0.3:
    #                 analysis.update({
    #                     'is_crouching': True,
    #                     'risk_level': 'high',
    #                     'description': 'Abnormal Crouching / Stuck Detected'
    #                 })
    #     except (KeyError, ZeroDivisionError):
    #         pass
    #     except Exception as e:
    #         logger.warning(f"웅크림 자세 분석 중 오류: {e}")
    #
    #     return analysis
    #
    # def draw_poses(self, frame: np.ndarray, detected_poses: List[Dict[str, Any]]) -> np.ndarray:
    #     """
    #     탐지된 자세 정보(관절, BBox, 분석 결과)를 프레임에 시각화합니다.
    #     """
    #     result_frame = frame.copy()
    #     if not detected_poses:
    #         return result_frame
    #
    #     for pose in detected_poses:
    #         bbox = pose['bbox']
    #         analysis = pose['analysis']
    #         keypoints = pose['keypoints']
    #
    #         color = (0, 255, 0) # 기본 초록색
    #         if analysis['risk_level'] == 'high':
    #             color = (0, 165, 255) # 주황색
    #         elif analysis['risk_level'] == 'critical':
    #             color = (0, 0, 255) # 빨간색
    #
    #         cv2.rectangle(result_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    #         label = f"Risk: {analysis['description']}"
    #         cv2.putText(result_frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    #
    #         # 관절 그리기
    #         for name, kp in keypoints.items():
    #             cv2.circle(result_frame, (int(kp[0]), int(kp[1])), 3, color, -1)
    #
    #     return result_frame
