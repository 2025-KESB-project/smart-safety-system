from typing import Dict, Any, List
from loguru import logger

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
        logger.info("RuleEngine 초기화 완료.")

    def decide_actions(self, mode: str, risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        현재 상태에 따라 수행해야 할 행동 목록을 결정합니다.

        Args:
            mode: ModeManager가 판단한 현재 작업 모드 ('normal_work' or 'abnormal_work')
            risk_analysis: RiskEvaluator가 평가한 위험 분석 결과

        Returns:
            수행할 행동을 나타내는 딕셔너리 리스트
            e.g., [{"type": "STOP_POWER", "details": {"reason": "critical_risk"}}]
        """
        actions = []
        risk_level = risk_analysis.get("risk_level", "safe")
        risk_details = risk_analysis.get("details", {})

        # --- 규칙 정의 ---

        # 규칙 1: 컨베이어 작동 멈춤 (stopped) 모드
        if mode == "stopped":
            # LOTO 기능: 위험 구역에 사람이 있거나 센서 알림 시 전원 투입 방지
            if risk_level != "safe": # 위험이 감지되면
                actions.append({"type": "PREVENT_POWER_ON", "details": {"reason": "person_in_danger_zone", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"level": "critical", "risk_details": risk_details}})
                actions.append({"type": "LOG_LOTO_ACTIVE", "details": {"risk_level": risk_level, "risk_details": risk_details}})
                logger.critical("규칙 적용: 작동 멈춤 모드 중 위험 감지 -> LOTO 활성화")
            else: # 안전하게 멈춰있는 상태
                actions.append({"type": "ALLOW_POWER_ON", "details": {"reason": "safe_to_operate"}})
                actions.append({"type": "LOG_STOPPED_SAFE", "details": {}})
                logger.info("규칙 적용: 작동 멈춤 모드 중 안전 -> 전원 투입 가능")

        # 규칙 2: 컨베이어 작동 중 (operating) 모드
        else: # mode == "operating"
            if risk_level == "critical":
                actions.append({"type": "STOP_POWER", "details": {"reason": "critical_risk_detected", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"level": "critical", "risk_details": risk_details}})
                actions.append({"type": "LOG_CRITICAL_INCIDENT", "details": {"risk_level": risk_level, "risk_details": risk_details}})
                logger.error("규칙 적용: 작동 중 심각 위험 감지 -> 즉시 정지")
            
            elif risk_level == "high":
                actions.append({"type": "SLOW_DOWN_50_PERCENT", "details": {"reason": "high_risk_detected", "risk_level": risk_level}})
                actions.append({"type": "TRIGGER_ALARM_HIGH", "details": {"level": "high", "risk_details": risk_details}})
                actions.append({"type": "LOG_HIGH_RISK", "details": {"risk_level": risk_level, "risk_details": risk_details}})
                logger.warning("규칙 적용: 작동 중 높은 위험 감지 -> 감속")

            elif risk_level == "medium":
                actions.append({"type": "TRIGGER_ALARM_MEDIUM", "details": {"level": "medium", "risk_details": risk_details}})
                actions.append({"type": "LOG_MEDIUM_RISK", "details": {"risk_level": risk_level, "risk_details": risk_details}})
                logger.info("규칙 적용: 작동 중 중간 위험 감지 -> 경고만")
            else: # safe
                actions.append({"type": "LOG_NORMAL_OPERATION", "details": {}})
                logger.info("규칙 적용: 작동 중 안전 -> 정상 작동")

        # 모든 위험 상황에 대해 UI 알림
        if risk_level != "safe":
            actions.append({"type": "NOTIFY_UI", "details": {"message": f"Risk detected: {risk_level.upper()}!", "risk_level": risk_level, "risk_details": risk_details}})

        return actions