from typing import Dict, Any, List
from loguru import logger

class RiskEvaluator:
    """
    Detection Layer의 결과를 바탕으로 잠재적 위험 요소를 식별하고 목록화합니다.
    """

    def __init__(self, config: Dict = None):
        """
        RiskEvaluator를 초기화합니다.
        """
        self.config = config or {}
        logger.info("RiskEvaluator 초기화 완료. (사실 기반)")

    def evaluate(self, detection_result: Dict[str, Any], sensor_data: Dict[str, Any], conveyor_status: bool) -> Dict[str, Any]:
        """
        탐지 결과를 종합하여 위험 요소를 식별하고 사실 목록을 반환합니다.

        Args:
            detection_result: Detector.detect()의 반환값
            sensor_data: InputAdapter에서 제공하는 센서 데이터
            conveyor_status: 현재 컨베이어 작동 상태

        Returns:
            위험 요소 목록을 포함한 딕셔너리
            e.g., {
                "risk_factors": [
                    {"type": "POSTURE_FALLING", "person_id": 1},
                    {"type": "ZONE_INTRUSION", "details": {...}}
                ]
            }
        """
        risk_factors = []

        # 1. 자세 분석 기반 위험 요소 식별
        persons = detection_result.get("persons", [])
        for i, person in enumerate(persons):
            analysis = person.get("pose_analysis", {})
            if analysis.get("is_falling"):
                risk_factors.append({"type": "POSTURE_FALLING", "person_id": i})
            elif analysis.get("is_crouching"):
                risk_factors.append({"type": "POSTURE_CROUCHING", "person_id": i})

        # 2. 위험 구역 침입 사실 식별
        zone_alerts = detection_result.get("danger_zone_alerts", [])
        if zone_alerts:
            # 침입이 한 건이라도 있으면 사실로 추가. 상세 정보는 details에 포함.
            risk_factors.append({
                "type": "ZONE_INTRUSION",
                "details": zone_alerts
            })

        # 3. 센서 데이터 기반 위험 요소 식별
        for sensor_type, sensor_info in sensor_data.get("sensors", {}).items():
            if sensor_info.get("is_alert"):
                risk_factors.append({
                    "type": "SENSOR_ALERT",
                    "sensor_type": sensor_type
                })

        return {"risk_factors": risk_factors}