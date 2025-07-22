import cv2
import numpy as np
import json
from typing import List, Dict, Any
from loguru import logger
from .danger_zone_mapper import DangerZoneMapper

class ZoneCreator:
    """사용자가 마우스로 위험 구역을 설정하도록 돕는 클래스"""

    def __init__(self, window_name: str, config_path: str, danger_zone_mapper: DangerZoneMapper):
        self.window_name = window_name
        self.config_path = config_path
        self.dz_mapper = danger_zone_mapper

        self.is_drawing = False
        self.points = []

        # 마우스 콜백 함수 설정
        # args1 : name of window, args2 : callback function
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        logger.info("ZoneCreator가 초기화되었습니다. 'd' 키를 눌러 구역 그리기를 시작하세요.")

    def _mouse_callback(self, event, x, y, flags, param):
        """마우스 이벤트가 발생할 때 호출될 함수"""
        if self.is_drawing:
            # 왼쪽 버튼 클릭 시, 현재 위치를 점으로 추가
            if event == cv2.EVENT_LBUTTONDOWN:
                self.points.append([x, y])
                logger.debug(f"점 추가: ({x}, {y}). 현재 점 개수: {len(self.points)}")
            # 오른쪽 버튼 클릭 시, 마지막 점 삭제 (실수 방지용)
            elif event == cv2.EVENT_RBUTTONDOWN:
                if self.points:
                    removed_point = self.points.pop()
                    logger.debug(f"점 삭제: {removed_point}. 현재 점 개수: {len(self.points)}")

    def _save_zone_to_config(self, new_zone_data: Dict):
        """새로운 구역 정보를 JSON 파일에 저장"""
        try:
            # 기존 설정 파일 읽기
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    all_zones_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_zones_data = []  # 파일이 없거나 비어있으면 새로 시작

            # 새로운 구역 추가
            all_zones_data.append(new_zone_data)

            # 파일에 다시 쓰기
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(all_zones_data, f, indent=2, ensure_ascii=False)
            logger.success(f"새로운 위험 구역 '{new_zone_data['name']}'을(를) '{self.config_path}'에 저장했습니다.")

        except Exception as e:
            logger.error(f"설정 파일 저장 중 오류 발생: {e}")

    def start_drawing(self):
        """그리기 모드를 활성화합니다."""
        self.is_drawing = True
        self.points = []
        logger.info("구역 그리기를 시작합니다. 마우스 왼쪽 버튼으로 점을 찍으세요. (오른쪽 버튼: 마지막 점 취소)")

    def cancel_drawing(self):
        """그리기 모드를 비활성화하고 초기화합니다."""
        self.is_drawing = False
        self.points = []
        logger.info("구역 그리기를 취소했습니다.")

    def save_current_zone(self, zone_id: str, zone_name: str):
        """현재 그려진 구역을 전달받은 정보로 저장합니다."""
        if not self.is_drawing or len(self.points) < 3:
            logger.warning("저장할 구역이 없거나, 점이 3개 미만입니다.")
            self.cancel_drawing()
            return False

        if zone_id and zone_name:
            new_zone_data = {
                "id": zone_id,
                "name": zone_name,
                "points": self.points,
                "iou_threshold": 0.2
            }
            self.dz_mapper.add_zone(new_zone_data)
            self._save_zone_to_config(new_zone_data)
            self.cancel_drawing()
            return True
        else:
            logger.warning("Zone ID 또는 이름이 제공되지 않아 저장을 취소합니다.")
            self.cancel_drawing()
            return False

    def draw_creation_feedback(self, frame: np.ndarray) -> np.ndarray:
        """그리기 모드일 때, 현재 상태를 프레임에 그려서 반환합니다."""
        if not self.is_drawing:
            return frame

        overlay = frame.copy()
        # 안내 메시지 표시
        cv2.putText(overlay, "Drawing Mode: Left-click to add point, Right-click to undo", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(overlay, "Press 's' to save, 'c' to cancel", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 0), 2)

        # 현재까지 찍은 점들을 선으로 연결하여 보여줌
        if len(self.points) > 0:
            pts = np.array(self.points, np.int32)
            cv2.polylines(overlay, [pts], isClosed=False, color=(255, 255, 0), thickness=2)
            for point in self.points:
                cv2.circle(overlay, tuple(point), 5, (0, 255, 255), -1)
        
        return overlay
