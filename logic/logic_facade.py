from typing import Dict, Any, List
from loguru import logger

from .risk_evaluator import RiskEvaluator
from .rule_engine import RuleEngine
# ControlFacade는 더 이상 LogicFacade에서 직접 사용하지 않습니다.
# from control.control_facade import ControlFacade

class LogicFacade:
    """
    Logic Layer의 모든 구성 요소를 통합하여 단순화된 인터페이스를 제공하는 퍼사드 클래스.
    """

    def __init__(self, config: Dict = None):
        """
        LogicFacade를 초기화하고 하위 모듈들을 생성합니다.
        
        Args:
            config: Logic Layer 전체 설정
            service_facade: (현재 사용되지 않음) 향후 로직 레이어에서 서비스가 필요할 경우를 대비.
        """
        config = config or {}
        self.risk_evaluator = RiskEvaluator(config.get("risk_evaluator"))
        self.rule_engine = RuleEngine(config.get("rule_engine"))
        
        # ControlFacade는 더 이상 LogicFacade에서 초기화하거나 사용하지 않습니다.
        # control_config = config.get("control", {})
        # self.control_facade = ControlFacade(service_facade=service_facade, **control_config)
        # Mode manager 사용하지 않습니다.
        
        self.last_risk_analysis = None # 마지막 위험 분석 결과를 저장
        
        logger.info("LogicFacade 및 모든 하위 로직 모듈 초기화 완료.")

    def process(self, detection_result: Dict[str, Any], sensor_data: Dict[str, Any], current_mode: str, current_conveyor_status: bool) -> List[Dict[str, Any]]:
        """
        전체 로직 파이프라인을 실행합니다.
        1. 위험도 평가
        2. 최종 행동 결정

        Args:
            detection_result: Detector.detect()의 반환값
            sensor_data: InputAdapter에서 제공하는 센서 데이터
            current_mode: SystemStateManager가 관리하는 현재 작업 모드 ('AUTOMATIC' 또는 'MAINTENANCE')
            current_conveyor_status: PowerController가 관리하는 현재 컨베이어 작동 상태 (True/False)

        Returns:
            RuleEngine이 결정한 최종 행동 목록
        """
        # 1. 위험도 평가
        # RiskEvaluator에 컨베이어 상태를 명시적으로 전달합니다.
        self.last_risk_analysis = self.risk_evaluator.evaluate(
            detection_result,
            sensor_data,
            conveyor_status=current_conveyor_status
        )
        
        # 2. 최종 행동 결정 (외부에서 전달받은 모드와 위험도 분석 결과를 기반으로)
        actions = self.rule_engine.decide_actions(current_mode, self.last_risk_analysis)
        
        # 3. 결정된 actions 목록을 그대로 반환하여 호출자(background_worker)가 처리하도록 합니다.
        return actions