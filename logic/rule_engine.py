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
        self.last_risk_factors = set() # 마지막 위험 요소를 기억하여 상태 변화를 감지
        logger.info("RuleEngine 초기화 완료. (사실 기반)")

    def decide_actions(self, mode: str, risk_analysis: Dict[str, Any], conveyor_is_on: bool, current_speed_percent: int) -> List[Dict[str, Any]]:
        """
        현재 상태에 따라 수행해야 할 행동 목록을 결정합니다.
        """
        actions = []
        risk_factors = risk_analysis.get("risk_factors", [])
        current_risk_types = {f["type"] for f in risk_factors}

        # --- 상태 변화 감지: 새로 생기거나 사라진 위험이 무엇인지 파악 ---
        newly_detected_risks = current_risk_types - self.last_risk_factors
        cleared_risks = self.last_risk_factors - current_risk_types
        
        # --- 위험 사실 존재 여부 확인 ---
        has_intrusion = "ZONE_INTRUSION" in current_risk_types
        is_falling = "POSTURE_FALLING" in current_risk_types
        is_crouching = "POSTURE_CROUCHING" in current_risk_types
        has_sensor_alert = "SENSOR_ALERT" in current_risk_types

        # --- 규칙 정의 ---
        log_action = None

        # 규칙 0: 비상 정지 조건 (모든 모드에서 최우선)
        if is_falling or has_sensor_alert:
            reason = "falling_detected" if is_falling else "sensor_alert"
            log_type = "LOG_CRITICAL_FALLING" if is_falling else "LOG_CRITICAL_SENSOR"
            actions.append({"type": "POWER_OFF", "details": {"reason": reason}})
            # 비상 상황은 새로 감지되었을 때만 경고를 울립니다.
            if newly_detected_risks:
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"reason": reason}})
            log_action = {"type": log_type, "details": {}}

        # 규칙 1: 정비(MAINTENANCE) 모드 - LOTO(Lock-Out, Tag-Out) 로직
        elif mode == "MAINTENANCE":
            # 정비 모드에서는 침입 여부와 관계없이 항상 전원을 차단합니다.
            if conveyor_is_on:
                actions.append({"type": "POWER_OFF", "details": {"reason": "maintenance_mode_active"}})
            
            # 정비 중 침입은 새로 감지되었을 때만 경고합니다.
            if has_intrusion and "ZONE_INTRUSION" in newly_detected_risks:
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"reason": "LOTO_zone_intrusion"}})
            log_action = {"type": "LOG_LOTO_ACTIVE", "details": {}}

        # 규칙 2: 운전(AUTOMATIC) 모드
        elif mode == "AUTOMATIC":
            if has_intrusion:
                if current_speed_percent != 50:
                    actions.append({"type": "REDUCE_SPEED_50", "details": {"reason": "zone_intrusion"}})
                # 침입이 새로 감지되었을 때만 경고를 시작합니다.
                if "ZONE_INTRUSION" in newly_detected_risks:
                    actions.append({"type": "TRIGGER_ALARM_HIGH", "details": {"reason": "intrusion"}})
                log_action = {"type": "LOG_INTRUSION_SLOWDOWN", "details": {}}
            elif is_crouching:
                # 웅크림이 새로 감지되었을 때만 경고를 시작합니다.
                if "POSTURE_CROUCHING" in newly_detected_risks:
                    actions.append({"type": "TRIGGER_ALARM_MEDIUM", "details": {"reason": "crouching"}})
                log_action = {"type": "LOG_CROUCHING_WARN", "details": {}}
            else:
                # 운전 모드이고, 아무 위험이 없으면 정상 운전
                # 이전에 울리던 경고가 있었다면, 모두 끄는 액션을 추가합니다.
                if "ZONE_INTRUSION" in cleared_risks:
                    actions.append({"type": "STOP_ALARM_HIGH"})
                if "POSTURE_CROUCHING" in cleared_risks:
                    actions.append({"type": "STOP_ALARM_MEDIUM"})

                # 전원이 꺼져 있을 때만 POWER_ON 명령을 내립니다.
                if not conveyor_is_on:
                    actions.append({"type": "POWER_ON", "details": {"reason": "normal_operation"}})
                
                # 속도가 100%가 아닐 때만 RESUME_FULL_SPEED 명령을 내립니다.
                if current_speed_percent < 100:
                    actions.append({"type": "RESUME_FULL_SPEED", "details": {"reason": "safety_zone_clear"}})
                
                log_action = {"type": "LOG_NORMAL_OPERATION", "details": {}}

        # --- 로깅 및 UI 알림 처리 ---
        
        # 1. 상태가 변경되었을 때만 로그 액션을 추가
        current_state_str = f"{mode}-{','.join(sorted(current_risk_types))}"
        if current_state_str != self.last_logged_state and log_action:
            actions.append(log_action)
            self.last_logged_state = current_state_str

        # 2. 위험이 새로 감지되었을 때만 UI 알림을 보냅니다.
        if newly_detected_risks:
            level = "safe"
            message = ""
            if "POSTURE_FALLING" in newly_detected_risks:
                level, message = "critical", "넘어짐 감지! 즉시 정지합니다."
            elif "SENSOR_ALERT" in newly_detected_risks:
                level, message = "critical", "비상 센서 감지! 즉시 정지합니다."
            elif "ZONE_INTRUSION" in newly_detected_risks:
                level, message = "high", "위험 구역 침입 감지!"
            elif "POSTURE_CROUCHING" in newly_detected_risks:
                level, message = "medium", "웅크린 자세 감지. 주의가 필요합니다."

            if level != "safe":
                notification_details = {
                    "type": "SYSTEM_ALERT",
                    "level": level,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                actions.append({"type": "NOTIFY_UI", "details": notification_details})

        # 마지막 위험 상태를 현재 상태로 업데이트합니다.
        self.last_risk_factors = current_risk_types

        return actions