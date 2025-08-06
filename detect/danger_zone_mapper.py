
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger
import threading

class DangerZoneMapper:
    """다각형 위험 구역을 설정하고, 사람의 침입 여부를 정교하게 판단합니다.
       이 클래스는 외부로부터 구역 데이터를 수동적으로 받아 업데이트됩니다.
    """

    def __init__(self):
        """
        위험 구역 매퍼를 초기화합니다.
        """
        self.danger_zones = []
        self._lock = threading.Lock()  # 스레드 안전성을 위한 잠금 장치
        logger.info("DangerZoneMapper 초기화 완료. (수동 업데이트 모드)")

    

    def update_zones_from_data(self, zones_data: List[Dict[str, Any]]):
        """외부에서 받은 데이터로 메모리의 위험 구역을 전체 업데이트합니다."""
        logger.info(f"DangerZoneMapper를 외부 데이터로 업데이트합니다. {len(zones_data)}개의 구역을 로드합니다.")
        new_zones = []
        for zone_data in zones_data:
            # add_zone 메소드를 재활용하여 파싱 및 추가 로직을 수행합니다.
            self.add_zone(zone_data, target_list=new_zones)
        
        with self._lock:
            self.danger_zones = new_zones
        logger.success(f"DangerZoneMapper가 {len(self.danger_zones)}개의 위험 구역으로 업데이트되었습니다.")

    def add_zone(self, zone_data: Dict[str, Any], target_list: List = None):
        """메모리에 위험 구역을 추가합니다. (DB 저장 X)
           target_list를 지정하여 특정 리스트에 추가할 수 있습니다.
        """
        try:
            zone_id = zone_data.get('id', 'N/A')
            zone_name = zone_data.get('name', 'Unknown Zone')
            points_list = [[p['x'], p['y']] for p in zone_data['points']]
            points = np.array(points_list, dtype=np.int32)
            iou_threshold = zone_data.get('iou_threshold', 0.2)

            if points.size == 0:
                logger.warning(f"Zone '{zone_name}' ({zone_id}) has no points.")
                return

            zone = {
                "id": zone_id,
                "name": zone_name,
                "points": points,
                "iou_threshold": iou_threshold,
                "bounding_rect": cv2.boundingRect(points)
            }
            
            # target_list가 주어지면 거기에 추가, 아니면 self.danger_zones에 추가
            if target_list is not None:
                target_list.append(zone)
            else:
                with self._lock:
                    self.danger_zones.append(zone)

        except (KeyError, TypeError) as e:
            logger.error(f"위험 구역 데이터에 필수 키가 없습니다: {e}. 데이터: {zone_data}")

    def check_person_in_zone(self, person_bbox: List[int], zone: Dict[str, Any]) -> Tuple[bool, float]:
        """
        사람이 위험 구역에 있는지 하이브리드 방식으로 정교하게 판단합니다.
        1. 주요 포인트 검사로 대부분의 케이스를 빠르게 판단합니다.
        2. 포인트 검사에서 놓치는 특수한 경우(작은 구역에 큰 객체)를 위해 IoU를 계산하여 보완합니다.

        Args:
            person_bbox: 사람 바운딩 박스 [x1, y1, x2, y2]
            zone: 구역 정보

        Returns:
            (침입 여부, 신뢰도(IoU 또는 1.0))
        """
        px1, py1, px2, py2 = person_bbox
        person_rect_points = np.array([[px1, py1], [px2, py1], [px2, py2], [px1, py2]], dtype=np.int32)

        # --- 1단계: 빠른 포인트 검사 ---
        key_points = [
            (px1, py1), (px2, py1), (px1, py2), (px2, py2), # 네 모서리
            ((px1 + px2) // 2, py2) # 발 위치
        ]
        for point in key_points:
            if cv2.pointPolygonTest(zone['points'], point, False) >= 0:
                return True, 1.0 # 주요 포인트가 하나라도 들어가면 즉시 침입으로 확정

        # --- 2단계: 정교한 교차 영역(Intersection) 계산 ---
        try:
            person_area = (px2 - px1) * (py2 - py1)
            if person_area == 0: return False, 0.0

            # 두 다각형(사람 bbox, 위험 구역)의 교차 영역을 계산
            # 1. 두 다각형을 모두 포함하는 빈 마스크(검은 이미지) 생성
            mask = np.zeros((max(py2, zone['bounding_rect'][1] + zone['bounding_rect'][3]), 
                               max(px2, zone['bounding_rect'][0] + zone['bounding_rect'][2])), dtype=np.uint8)
            
            # 2. 마스크에 사람의 바운딩 박스를 흰색으로 채움
            cv2.fillPoly(mask, [person_rect_points], 255)
            person_mask = mask.copy()

            # 3. 마스크에 위험 구역 다각형을 흰색으로 채움
            mask.fill(0)
            cv2.fillPoly(mask, [zone['points']], 255)
            zone_mask = mask

            # 4. 두 마스크에 대해 비트 AND 연산을 수행하여 교차 영역 마스크를 얻음
            intersection_mask = cv2.bitwise_and(person_mask, zone_mask)

            # 5. 교차 영역의 면적(흰색 픽셀의 개수)을 계산
            intersection_area = cv2.countNonZero(intersection_mask)

            # 6. 사람 면적 대비 교차 영역의 비율(IoU)을 계산
            iou = intersection_area / person_area

            is_in_zone = iou >= zone['iou_threshold']
            return is_in_zone, round(iou, 2)

        except Exception as e:
            logger.warning(f"교차 영역 계산 중 오류 발생: {e}")
            return False, 0.0

    def check_all_zones(self, persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        모든 위험 구역에 대해 침입 검사를 수행하고 상세 정보를 반환합니다.

        Args:
            persons: 감지된 사람 리스트

        Returns:
            위험 구역별 침입 상세 정보 리스트
        """
        alerts = []
        for zone in self.danger_zones:
            persons_in_zone = []
            for i, person in enumerate(persons):
                is_in, iou = self.check_person_in_zone(person["bbox"], zone)
                if is_in:
                    persons_in_zone.append({
                        "person_index": i,
                        "bbox": person["bbox"],
                        "confidence": person["confidence"],
                        "intrusion_iou": round(iou, 2)
                    })
            
            if persons_in_zone:
                alerts.append({
                    "zone_id": zone["id"],
                    "zone_name": zone["name"],
                    "person_count": len(persons_in_zone),
                    "persons": persons_in_zone
                })
        return alerts

    def visualize_zones(self, frame: np.ndarray, alerts: List[Dict] = None) -> np.ndarray:
        """
        위험 구역과 침입 상태를 프레임에 그립니다.

        Args:
            frame: 원본 프레임
            alerts: check_all_zones의 결과. 침입 시 구역 색상을 변경하는 데 사용됩니다.

        Returns:
            구역이 그려진 프레임
        """
        result_frame = frame.copy()
        alert_zone_ids = {alert['zone_id'] for alert in alerts} if alerts else set()

        for zone in self.danger_zones:
            color = (0, 0, 255) if zone['id'] in alert_zone_ids else (0, 255, 0) # 침입 시 빨간색, 평시 초록색
            thickness = 4 if zone['id'] in alert_zone_ids else 2

            cv2.polylines(result_frame, [zone['points']], isClosed=True, color=color, thickness=thickness)
            
            label_pos = (zone['bounding_rect'][0], zone['bounding_rect'][1] - 10)
            cv2.putText(result_frame, zone["name"], label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return result_frame
