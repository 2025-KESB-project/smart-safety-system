import cv2
import time
from loguru import logger
import sys
from pathlib import Path

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from control.control_facade import ControlFacade

# --- 중앙 설정 (테스트용) ---
CONFIG = {
    'input': {
        'camera_index': 0,
        'mock_mode': False
    },
    'detector': {
        'person_detector': {'model_path': 'yolov8n.pt', 'conf_threshold': 0.4},
        'pose_detector': {
            'pose_model_path': 'yolov8n-pose.pt',
            'fall_model_path': 'fall_det_1.pt',
            'conf_threshold': 0.5
        }
    },
    'control': {
        'mock_mode': False,
        'serial_port': 'COM9',
        'baud_rate': 9600
    },
    'logic': {}
}

# --- 테스트용 Mock Service ---
class MockZoneService:
    """테스트를 위해 하드코딩된 위험 구역 데이터를 제공하는 가짜 서비스"""
    def get_all_zones(self):
        logger.info("[Mock] 테스트용 위험 구역 데이터를 반환합니다.")
        # 화면 중앙에 사각형 위험 구역을 정의 (640x480 카메라 기준)
        return [
            {
                'id': 'mock_zone_1',
                'name': 'Center Test Zone',
                'points': [
                    {'0': 220, '1': 140}, # Top-left
                    {'0': 420, '1': 140}, # Top-right
                    {'0': 420, '1': 340}, # Bottom-right
                    {'0': 220, '1': 340}  # Bottom-left
                ]
            }
        ]

    def register_listener(self, callback):
        # 테스트 중에는 리스너를 등록할 필요가 없으므로 아무것도 하지 않음
        logger.info("[Mock] Zone listener 등록 요청을 무시합니다.")
        pass

def main():
    """통합 테스트 메인 함수"""
    logger.info("--- 정형 모드 위험 구역 침입 감속 테스트 시작 ---")

    # 1. 각 계층의 Facade 초기화
    try:
        input_facade = InputAdapter(**CONFIG.get('input', {}))
        
        # DB 대신 MockZoneService를 사용하도록 설정
        mock_zone_service = MockZoneService()
        detector = Detector(config=CONFIG.get('detector', {}), zone_service=mock_zone_service)
        
        control_facade = ControlFacade(**CONFIG.get('control', {}))
        logic_facade = LogicFacade(config=CONFIG.get('logic', {}), service_facade=None)
        logger.success("모든 Facade 초기화 완료.")
    except Exception as e:
        logger.critical(f"Facade 초기화 중 오류 발생: {e}")
        return

    # 2. 테스트 시나리오 준비: 컨베이어를 100% 속도로 시작 (정형 모드)
    logger.info("시나리오 시작: 컨베이어를 100% 속도로 가동합니다.")
    # 초기 속도를 0으로 설정하여 resume_full_speed가 실제로 명령을 보내도록 함
    control_facade.speed_controller.set_speed(0, "Initial setup")
    time.sleep(0.5) # 아두이노가 명령을 처리할 시간
    control_facade.speed_controller.resume_full_speed(reason="Test Start")
    time.sleep(1) # 모터가 작동할 시간을 줌

    # 3. 메인 루프 실행
    try:
        while True:
            frame_time = time.time()

            # 입력 계층: 데이터 수집
            input_data = input_facade.get_input()
            if input_data is None or 'raw_frame' not in input_data:
                logger.warning("입력 소스에서 데이터를 받아오지 못했습니다. 1초 후 재시도...")
                time.sleep(1)
                continue
            
            frame = input_data['raw_frame']
            # 테스트에서는 센서 데이터를 빈 값으로 처리
            sensor_data = {'sensors': {}}

            # 탐지 계층: 객체 및 위험 구역 분석
            detection_result = detector.detect(frame)

            # 로직 계층: 위험 판단 및 제어 명령 생성
            # 정형 모드(작동 중)를 가정하기 위해 is_conveyor_operating 값을 True로 강제
            sensor_data['sensors']['conveyor_operating'] = {'value': 1}
            actions = logic_facade.process(detection_result=detection_result, sensor_data=sensor_data)
            
            # 제어 계층: 명령 실행
            if actions:
                logger.debug(f"실행할 조치: {actions}")
                control_facade.execute_actions(actions)

            # 시각화
            processed_frame = detector.draw_detections(frame, detection_result)
            fps = 1 / (time.time() - frame_time)
            cv2.putText(processed_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Formal Mode Test", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("'q' 입력으로 테스트를 종료합니다.")
                break

    except KeyboardInterrupt:
        logger.info("Ctrl+C 입력으로 테스트를 종료합니다.")
    except Exception as e:
        logger.error(f"메인 루프 실행 중 예외 발생: {e}", exc_info=True)
    finally:
        # 자원 해제
        logger.info("자원을 해제합니다...")
        control_facade.speed_controller.stop_conveyor(reason="Test End") # 테스트 종료 시 모터 정지
        input_facade.release()
        control_facade.release()
        cv2.destroyAllWindows()
        logger.info("--- 통합 테스트 종료 ---")

if __name__ == "__main__":
    main()