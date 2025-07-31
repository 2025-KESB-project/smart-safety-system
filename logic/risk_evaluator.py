from typing import Dict, Any, List
from loguru import logger

class RiskEvaluator:
    """
    Detection Layer의 결과를 바탕으로 잠재적 위험을 평가하고 정량화합니다.
    """

    def __init__(self, config: Dict = None):
        """
        RiskEvaluator를 초기화합니다.
        
        Args:
            config: 위험 평가 관련 설정 (e.g., 위험 점수 가중치)
        """
        self.config = config or {}
        logger.info("RiskEvaluator 초기화 완료.")

    def evaluate(self, detection_result: Dict[str, Any], sensor_data: Dict[str, Any], conveyor_status: bool) -> Dict[str, Any]:
        """
        탐지 결과를 종합하여 위험도를 평가합니다.

        Args:
            detection_result: Detector.detect()의 반환값
            sensor_data: InputAdapter에서 제공하는 센서 데이터
            conveyor_status: 현재 컨베이어 작동 상태 (True/False). 현재 로직에서는 사용되지 않으나, 향후 확장을 위해 전달받음.

        Returns:
            위험 평가가 추가된 분석 결과 딕셔너리
            e.g., {
                "risk_level": "critical",
                "risk_score": 95,
                "details": [
                    {"type": "falling", "description": "Person 1 is falling", "score": 90},
                    {"type": "zone_intrusion", "description": "2 persons in High-Risk Zone", "score": 50}
                ]
            }
        """
        evaluated_risks = {
            "risk_level": "safe",
            "risk_score": 0,
            "details": []
        }
        total_score = 0
        
        # 1. 통합된 person 객체 기반 위험 평가
        persons = detection_result.get("persons", [])
        for i, person in enumerate(persons):
            analysis = person.get("pose_analysis", {})
            if analysis.get("is_falling"):
                risk_detail = {
                    "type": "falling",
                    "person_id": i,
                    "description": f"Person {i} is falling.",
                    "score": 95  # 가장 높은 위험 점수
                }
                evaluated_risks["details"].append(risk_detail)
                total_score = max(total_score, risk_detail["score"])

            elif analysis.get("is_crouching"):
                risk_detail = {
                    "type": "crouching",
                    "person_id": i,
                    "description": f"Person {i} is in an abnormal crouching pose.",
                    "score": 70
                }
                evaluated_risks["details"].append(risk_detail)
                total_score = max(total_score, risk_detail["score"])

        # 2. 위험 구역 침입 기반 위험 평가
        alerts = detection_result.get("danger_zone_alerts", [])
        for alert in alerts:
            person_count = alert.get("person_count", 0)
            risk_detail = {
                "type": "zone_intrusion",
                "zone_id": alert.get("zone_id"),
                "zone_name": alert.get("zone_name"),
                "description": f"{person_count} person(s) detected in zone '{alert.get('zone_name')}'.",
                "score": 50 + (person_count - 1) * 10  # 침입 인원이 많을수록 위험
            }
            evaluated_risks["details"].append(risk_detail)
            total_score = max(total_score, risk_detail["score"])
            
        # 3. 센서 데이터 기반 위험 평가
        for sensor_type, sensor_info in sensor_data.get("sensors", {}).items():
            if sensor_info.get("is_alert"):
                risk_detail = {
                    "type": f"sensor_alert_{sensor_type}",
                    "description": f"Sensor {sensor_type} is in alert state.",
                    "score": 30 # 센서 알림 시 기본 점수
                }
                evaluated_risks["details"].append(risk_detail)
                total_score = max(total_score, risk_detail["score"])

        # 최종 위험 등급 및 점수 결정
        evaluated_risks["risk_score"] = total_score
        if total_score >= 90:
            evaluated_risks["risk_level"] = "critical"
        elif total_score >= 70:
            evaluated_risks["risk_level"] = "high"
        elif total_score >= 40:
            evaluated_risks["risk_level"] = "medium"
        
        return evaluated_risks