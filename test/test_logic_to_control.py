import sys
from pathlib import Path
import time
from loguru import logger

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from logic.logic_facade import LogicFacade
from control.control_facade import ControlFacade

def test_logic_to_control():
    """
    로직 계층과 제어 계층의 연동을 테스트합니다.
    가상의 '위험 구역 내 사람 감지' 데이터를 생성하여, 로직 계층이
    올바른 제어 명령을 생성하고, 제어 계층이 이를 실행하는지 확인합니다.
    """
    logger.info("--- 로직 -> 제어 계층 연동 테스트 시작 ---")

    # 1. 모듈 초기화
    try:
        logic_facade = LogicFacade()
        # mock_mode=True로 설정하여 하드웨어 연결 없이 테스트
        control_facade = ControlFacade(mock_mode=True)
        logger.success("LogicFacade와 ControlFacade 초기화 완료 (모의 제어 모드).")
    except Exception as e:
        logger.error(f"모듈 초기화 실패: {e}")
        return

    # 2. 테스트 시나리오 정의: "운영 중인 컨베이어의 위험 구역에 사람이 들어옴"
    logger.info("테스트 시나리오: '운영 중인 컨베이어의 위험 구역에 사람이 들어옴'")
    
    # 가상 탐지 데이터 생성
    # RiskEvaluator가 이 구조를 보고 위험 등급을 'high'로 판단해야 함
    mock_detection_result = {
        'persons': [{'person_id': 0, 'bbox': [100, 100, 200, 400]}],
        'poses': [{'person_id': 0, 'analysis': {'is_falling': False, 'is_crouching': False}}],
        'danger_zone_alerts': [  # 'danger_zone' -> 'danger_zone_alerts'로 키 변경 및 리스트로 감싸기
            {
                "zone_id": "zone_01",
                "zone_name": "High-Risk-Zone",
                "person_count": 1,
                "person_ids": {0}
            }
        ]
    }
    
    # 가상 센서 데이터 생성
    mock_sensor_data = {
        "is_conveyor_operating": True # 컨베이어가 작동 중임을 의미
    }
    
    logger.info(f"가상 탐지 데이터: {mock_detection_result}")
    logger.info(f"가상 센서 데이터: {mock_sensor_data}")

    # 3. 로직 계층 실행 -> 제어 명령 생성
    logger.info("LogicFacade를 통해 제어 명령을 생성합니다...")
    commands = logic_facade.process(mock_detection_result, mock_sensor_data)
    
    if not commands:
        logger.error("로직 계층에서 아무런 제어 명령도 생성되지 않았습니다. 로직을 확인하세요.")
        return
        
    logger.success(f"생성된 제어 명령: {commands}")

    # 4. 제어 계층 실행 -> 아두이노 제어
    logger.info(f"ControlFacade를 통해 '{commands}' 명령을 실행합니다.")
    logger.warning(">>> 지금부터 실제 아두이노의 동작(모터 감속, LED 점등 등)을 확인해주세요. <<<")
    
    control_facade.execute_actions(commands)

    # 사용자가 결과를 확인할 수 있도록 5초간 대기
    time.sleep(5)

    # 5. 테스트 종료 및 초기화
    logger.info("테스트를 위해 보냈던 제어 신호를 초기화합니다.")
    # 테스트 종료 후 안전한 상태로 되돌리기 위해 'ALLOW_POWER_ON' 명령을 다시 보냅니다.
    reset_command = [{'type': 'ALLOW_POWER_ON', 'details': {'reason': 'test_finished'}}]
    control_facade.execute_actions(reset_command)
    
    logger.info("--- 테스트 종료 ---")


if __name__ == '__main__':
    test_logic_to_control()
