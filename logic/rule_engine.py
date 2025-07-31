from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

class RuleEngine:
    """
    작업 모드와 식별된 위험 사실 목록을 바탕으로 최종 시스템 행동을 결정하는 규칙 기반 엔진.
    """

    def __init__(self, config: Dict = None):
        """
        RuleEngine을 초기화합니다.
        """
        self.config = config or {}
        self.last_logged_state = None # 마지막으로 로깅한 상태를 저장
        logger.info("RuleEngine 초기화 완료. (사실 기반)")

    def decide_actions(self, mode: str, risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        현재 상태에 따라 수행해야 할 행동 목록을 결정합니다.

        Args:
            mode: SystemStateManager가 제공하는 현재 작업 모드 ('AUTOMATIC' or 'MAINTENANCE')
            risk_analysis: RiskEvaluator가 평가한 위험 사실 목록

        Returns:
            수행할 행동을 나타내는 딕셔너리 리스트
        """
        actions = []
        risk_factors = risk_analysis.get("risk_factors", [])
        
        # --- 위험 사실 존재 여부 확인 ---
        has_intrusion = any(f["type"] == "ZONE_INTRUSION" for f in risk_factors)
        is_falling = any(f["type"] == "POSTURE_FALLING" for f in risk_factors)
        is_crouching = any(f["type"] == "POSTURE_CROUCHING" for f in risk_factors)
        has_sensor_alert = any(f["type"] == "SENSOR_ALERT" for f in risk_factors)

        # --- 규칙 정의 ---
        log_action = None

        # 규칙 0: 비상 정지 조건 (모든 모드에서 최우선)
        if is_falling or has_sensor_alert:
            reason = "falling_detected" if is_falling else "sensor_alert"
            log_type = "LOG_CRITICAL_FALLING" if is_falling else "LOG_CRITICAL_SENSOR"
            actions.append({"type": "POWER_OFF", "details": {"reason": reason}})
            actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"reason": reason}})
            log_action = {"type": log_type, "details": {}}

        # 규칙 1: 정비(MAINTENANCE) 모드 - LOTO(Lock-Out, Tag-Out) 로직
        elif mode == "MAINTENANCE":
            if has_intrusion:
                actions.append({"type": "POWER_OFF", "details": {"reason": "LOTO_zone_intrusion"}})
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"reason": "LOTO"}})
                log_action = {"type": "LOG_LOTO_ACTIVE", "details": {}}
            else:
                # 정비 모드이고, 침입이 없으면 아무것도 하지 않음 (전원 인가 방지)
                log_action = {"type": "LOG_MAINTENANCE_SAFE", "details": {}}

        # 규칙 2: 운전(AUTOMATIC) 모드
        elif mode == "AUTOMATIC":
            if has_intrusion:
                actions.append({"type": "REDUCE_SPEED_50", "details": {"reason": "zone_intrusion"}})
                actions.append({"type": "TRIGGER_ALARM_HIGH", "details": {"reason": "intrusion"}})
                log_action = {"type": "LOG_INTRUSION_SLOWDOWN", "details": {}}
            elif is_crouching:
                # 웅크린 자세는 위험 구역 밖에서는 경고만.
                actions.append({"type": "TRIGGER_ALARM_MEDIUM", "details": {"reason": "crouching"}})
                log_action = {"type": "LOG_CROUCHING_WARN", "details": {}}
            else:
                # 운전 모드이고, 아무 위험이 없으면 정상 운전
                actions.append({"type": "POWER_ON", "details": {"reason": "normal_operation"}})
                log_action = {"type": "LOG_NORMAL_OPERATION", "details": {}}

        # --- 로깅 및 UI 알림 처리 ---
        
        # 1. 상태가 변경되었을 때만 로그 액션을 추가
        factor_types = sorted([f["type"] for f in risk_factors])
        #AUTOMATIC-ZONE_INTRUSION 예시
        current_state = f"{mode}-{','.join(factor_types)}"
        if current_state != self.last_logged_state and log_action:
            actions.append(log_action)
            self.last_logged_state = current_state

        # 2. 위험 상황에 대해 UI 알림 (중복 알림 방지 필요 시 추가 로직 구현)
        if risk_factors:
            # UI에 보낼 가장 중요한 알림 하나를 선택 (예: 넘어짐/센서 > 침입 > 웅크림)
            level = "safe"
            message = ""
            if is_falling:
                level, message = "critical", "넘어짐 감지! 즉시 정지합니다."
            elif has_sensor_alert:
                level, message = "critical", "비상 센서 감지! 즉시 정지합니다."
            elif has_intrusion:
                level, message = "high", "위험 구역 침입 감지!"
            elif is_crouching:
                level, message = "medium", "웅크린 자세 감지. 주의가 필요합니다."

            if level != "safe":
                notification_details = {
                    "type": "SYSTEM_ALERT",
                    "level": level,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                actions.append({"type": "NOTIFY_UI", "details": notification_details})

        return actions