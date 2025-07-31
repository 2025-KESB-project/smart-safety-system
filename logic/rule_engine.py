from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

class RuleEngine:
    """
    작업 모드와 위험도를 바탕으로 최종 시스템 행동을 결정하는 규칙 기반 엔진.
    """

    def __init__(self, config: Dict = None):
        """
        RuleEngine을 초기화합니다.
        
        Args:
            config: 규칙 관련 설정
        """
        self.config = config or {}
        self.last_logged_state = None # 마지막으로 로깅한 상태를 저장
        logger.info("RuleEngine 초기화 완료.")

    def decide_actions(self, mode: str, risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        현재 상태에 따라 수행해야 할 행동 목록을 결정합니다.

        Args:
            mode: state_manager에서 app.state로 받습니다.
            risk_analysis: RiskEvaluator가 평가한 위험 분석 결과

        Returns:
            수행할 행동을 나타내는 딕셔너리 리스트
            e.g., [{"type": "STOP_POWER", "details": {"reason": "critical_risk"}}]
        """
        actions = []
        risk_level = risk_analysis.get("risk_level", "safe")
        risk_details = risk_analysis.get("details", {})

        current_state = f"{mode}-{risk_level}"
        log_action = None

        # --- 규칙 정의 ---

        # 규칙 1: 컨베이어 작동 멈춤 (MAINTENANCE) 모드
        if mode == "MAINTENANCE":
            # LOTO 기능: 위험 구역에 사람이 있거나 센서 알림 시 전원 투입 방지
            if risk_level != "safe": # 위험이 감지되면
                actions.append({"type": "PREVENT_POWER_ON", "details": {"reason": "person_in_danger_zone", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"level": "critical", "risk_details": risk_details}})
                log_action = {"type": "LOG_LOTO_ACTIVE", "details": {"risk_level": risk_level, "risk_details": risk_details}}
            else: # 안전하게 멈춰있는 상태
                actions.append({"type": "ALLOW_POWER_ON", "details": {"reason": "safe_to_operate"}})
                log_action = {"type": "LOG_STOPPED_SAFE", "details": {}}

        # 규칙 2: 컨베이어 작동 중 (AUTOMATIC) 모드
        else: # mode == "AUTOMATIC"
            if risk_level == "critical":
                actions.append({"type": "STOP_POWER", "details": {"reason": "critical_risk_detected", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"level": "critical", "risk_details": risk_details}})
                log_action = {"type": "LOG_CRITICAL_INCIDENT", "details": {"risk_level": risk_level, "risk_details": risk_details}}
            
            elif risk_level == "high":
                actions.append({"type": "SLOW_DOWN_50_PERCENT", "details": {"reason": "high_risk_detected", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_HIGH", "details": {"level": "high", "risk_details": risk_details}})
                log_action = {"type": "LOG_HIGH_RISK", "details": {"risk_level": risk_level, "risk_details": risk_details}}

            elif risk_level == "medium":
                actions.append({"type": "TRIGGER_ALARM_MEDIUM", "details": {"level": "medium", "risk_details": risk_details}})
                log_action = {"type": "LOG_MEDIUM_RISK", "details": {"risk_level": risk_level, "risk_details": risk_details}}
            else: # safe
                log_action = {"type": "LOG_NORMAL_OPERATION", "details": {}}

        # 상태가 변경되었을 때만 로그 액션을 추가
        if current_state != self.last_logged_state and log_action:
            actions.append(log_action)
            self.last_logged_state = current_state

        # 모든 위험 상황에 대해 UI 알림
        if risk_level != "safe":
            # 상세한 알림 메시지 생성
            if isinstance(risk_details, dict):
                reason = ', '.join(risk_details.keys())
            elif isinstance(risk_details, str):
                reason = risk_details
            else:
                reason = "알 수 없는 원인"
            
            alert_message = f"위험 수준 '{risk_level.upper()}' 감지. 원인: {reason}"
            
            # 웹소켓으로 보낼 상세 정보 구성 (AlertMessage 모델 형식 준수)
            notification_details = {
                "type": "SYSTEM_ALERT",
                "level": risk_level,
                "message": alert_message,
                "timestamp": datetime.now().isoformat() # ISO 8601 형식으로 변환
            }
            actions.append({"type": "NOTIFY_UI", "details": notification_details})

        return actions