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
        self.last_system_state = None # 마지막으로 결정된 시스템 상태를 저장
        logger.info("RuleEngine 초기화 완료. (상태 기반)")

    def decide_actions(self, mode: str, risk_analysis: Dict[str, Any], conveyor_is_on: bool, current_speed_percent: int) -> List[Dict[str, Any]]:
        """
        현재 상태에 따라 수행해야 할 행동 목록을 결정합니다.

        Args:
            mode: SystemStateManager가 제공하는 현재 작업 모드 ('AUTOMATIC' or 'MAINTENANCE')
            risk_analysis: RiskEvaluator가 평가한 위험 사실 목록
            conveyor_is_on: 현재 컨베이어 전원 상태
            current_speed_percent: 현재 컨베이어 속도 (%)

        Returns:
            수행할 행동을 나타내는 딕셔너리 리스트
        """
        actions = []
        risk_factors = risk_analysis.get("risk_factors", [])

        # 규칙 -1: 시스템 정지(STOP) 모드 (모든 규칙에 우선)
        if mode == "STOP":
            # 현재 전원이 켜져 있을 때만 POWER_OFF 명령을 내립니다.
            if conveyor_is_on:
                actions.append({"type": "POWER_OFF", "details": {"reason": "system_stopped_by_user"}})
            # 다른 모든 액션을 무시하고 즉시 반환합니다.
            return actions
        
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
            # 정비 모드에서는 침입 여부와 관계없이 항상 전원을 차단합니다.
            # 전원이 켜져 있을 때만 POWER_OFF 명령을 내립니다.
            if conveyor_is_on:
                actions.append({"type": "POWER_OFF", "details": {"reason": "maintenance_mode_active"}})
            
            if has_intrusion:
                # 침입이 있을 경우, 추가적으로 경고 및 로깅
                actions.append({"type": "TRIGGER_ALARM_CRITICAL", "details": {"reason": "LOTO_zone_intrusion"}})
                log_action = {"type": "LOG_LOTO_ACTIVE", "details": {}}
            else:
                # 침입이 없을 경우, 안전 상태 로깅
                log_action = {"type": "LOG_MAINTENANCE_SAFE", "details": {}}

        # 규칙 2: 운전(AUTOMATIC) 모드
        elif mode == "AUTOMATIC":
            if has_intrusion:
                # 속도가 50%가 아닐 때만 감속 명령을 내립니다.
                if current_speed_percent != 50:
                    actions.append({"type": "REDUCE_SPEED_50", "details": {"reason": "zone_intrusion"}})
                actions.append({"type": "TRIGGER_ALARM_HIGH", "details": {"reason": "intrusion"}})
                log_action = {"type": "LOG_INTRUSION_SLOWDOWN", "details": {}}
            elif is_crouching:
                # 웅크린 자세는 위험 구역 밖에서는 경고만.
                actions.append({"type": "TRIGGER_ALARM_MEDIUM", "details": {"reason": "crouching"}})
                log_action = {"type": "LOG_CROUCHING_WARN", "details": {}}
            else:
                # 운전 모드이고, 아무 위험이 없으면 정상 운전
                # 전원이 꺼져 있을 때만 POWER_ON 명령을 내립니다.
                if not conveyor_is_on:
                    actions.append({"type": "POWER_ON", "details": {"reason": "normal_operation"}})
                
                # 속도가 100%가 아닐 때만 RESUME_FULL_SPEED 명령을 내립니다.
                if current_speed_percent < 100:
                    actions.append({"type": "RESUME_FULL_SPEED", "details": {"reason": "safety_zone_clear"}})
                
                log_action = {"type": "LOG_NORMAL_OPERATION", "details": {}}

        # --- 로깅 처리 ---
        # 1. 결정된 시스템 상태(log_action)가 이전 상태와 다를 경우에만 로그 액션을 추가합니다.
        #    이를 통해 동일한 상태 로그가 반복적으로 쌓이는 것을 방지합니다.
        current_system_state = log_action['type'] if log_action else "NO_ACTION"

        if current_system_state != self.last_system_state:
            if log_action:
                actions.append(log_action)
            self.last_system_state = current_system_state

        return actions