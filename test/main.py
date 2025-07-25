import cv2
import time
from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector
from logic.mode_manager import ModeManager, WorkMode
from logic.risk_evaluator import RiskEvaluator
from logic.rule_engine import RuleEngine, Rule
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.test.alert_controller import AlertController
from server.services.logger_service import LoggerService

class SmartSafetySystem:
    """스마트 안전 시스템 메인 클래스"""

    def __init__(self, config):
        self.config = config
        self.input_adapter = InputAdapter(**config['input_adapter'])
        self.detector = Detector(config['detector'])
        self.mode_manager = ModeManager()
        self.risk_evaluator = RiskEvaluator()
        self.rule_engine = self._setup_rule_engine()
        self.power_controller = PowerController(**config['controllers']['power'])
        self.speed_controller = SpeedController(**config['controllers']['speed'])
        self.alert_controller = AlertController(**config['controllers']['alert'])
        self.logger = LoggerService()
        self.is_running = False

    def _setup_rule_engine(self):
        """Rule Engine을 설정하고 규칙을 추가합니다."""
        engine = RuleEngine()

        # 비정형 작업 모드 규칙
        irregular_mode_rule = Rule(
            name="IrregularModeSafety",
            condition=lambda data: data['mode'] == WorkMode.IRREGULAR and data['detection']['danger_analysis']['person_in_danger_zone'],
            action=lambda data: self.power_controller.emergency_off()
        )

        # 정형 작업 모드 규칙
        normal_mode_rule_warn = Rule(
            name="NormalModeWarning",
            condition=lambda data: data['mode'] == WorkMode.NORMAL and data['risk']['overall_risk'].value == 'high',
            action=lambda data: self.speed_controller.set_speed(50)
        )
        normal_mode_rule_stop = Rule(
            name="NormalModeStop",
            condition=lambda data: data['mode'] == WorkMode.NORMAL and data['risk']['overall_risk'].value == 'critical',
            action=lambda data: self.power_controller.turn_off()
        )

        engine.add_rule(irregular_mode_rule)
        engine.add_rule(normal_mode_rule_warn)
        engine.add_rule(normal_mode_rule_stop)
        return engine

    def run(self):
        """시스템의 메인 루프를 실행합니다."""
        self.is_running = True
        print("스마트 안전 시스템을 시작합니다.")

        while self.is_running:
            try:
                # 1. 입력 데이터 가져오기
                input_data = self.input_adapter.get_input()
                if input_data is None:
                    print("입력 스트림이 종료되었습니다.")
                    break

                # 2. 탐지 수행
                detection_result = self.detector.detect(input_data['frame'])

                # 3. 로직 처리 (모드, 위험도, 규칙)
                current_mode = self.mode_manager.get_current_mode()
                mode_config = self.mode_manager.get_mode_config(current_mode)
                risk_assessment = self.risk_evaluator.evaluate_risk(detection_result, mode_config)
                self.logger.log_event('risk_assessment', risk_assessment.dict())

                # 4. 규칙 엔진 실행
                logic_data = {
                    'mode': current_mode,
                    'detection': detection_result,
                    'risk': risk_assessment.dict() # RiskAssessment를 dict로 변환
                }
                self.rule_engine.execute(logic_data)

                # (임시) 현재 상태 출력
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Mode: {current_mode.value}, Risk: {risk_assessment.overall_risk.value}")

                # 종료 조건 (예: 'q' 키 입력)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()

            except KeyboardInterrupt:
                self.stop()
                break

    def stop(self):
        """시스템을 안전하게 종료합니다."""
        self.is_running = False
        self.input_adapter.release()
        print("스마트 안전 시스템을 종료합니다.")

if __name__ == '__main__':
    # 임시 설정값 - 추후 config.py에서 로드
    temp_config = {
        'input_adapter': {'camera_index': 0, 'mock_mode': True},
        'detector': {
            'yolo_model_path': 'yolov8n.pt',
            'danger_zones': [{'name': 'conveyor_zone', 'points': [[100, 100], [540, 100], [540, 380], [100, 380]]}]
        },
        'controllers': {
            'power': {'mock_mode': True},
            'speed': {'mock_mode': True},
            'alert': {'mock_mode': True}
        }
    }

    system = SmartSafetySystem(temp_config)
    system.run()