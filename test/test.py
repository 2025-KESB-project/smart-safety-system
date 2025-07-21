# test_realtime_pipeline.py

import cv2
import time
from pathlib import Path
from loguru import logger
import sys
from typing import Dict, Any

# --------------------------------------------------------------------------
# 시스템 경로 설정
# --------------------------------------------------------------------------
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from input_adapter.input_facade import InputAdapter
    from detect.detect_facade import Detector
    from logic.logic_facade import LogicFacade

    logger.info("모듈 경로 설정 완료.")
except ImportError as e:
    logger.error(f"모듈을 임포트할 수 없습니다. 스크립트를 프로젝트 루트에서 실행하고 있는지 확인하세요. 오류: {e}")
    sys.exit(1)

# --------------------------------------------------------------------------
# 테스트 설정 (하나의 CONFIG 딕셔너리로 통합)
# --------------------------------------------------------------------------
CONFIG = {
    'input': {
        'camera_index': 0,
        'mock_mode': False  # <<-- 실제 카메라 사용 시 False
    },
    'detector': {
        'person_detector': {'model_path': 'yolov8n.pt'},
        'pose_detector': {'model_path': 'yolov8n-pose.pt'},
        'danger_zone_mapper': {'zone_config_path': 'danger_zones.json'}
    },
    'control': {
        'mock_mode': True  # 모든 제어 모듈을 모의 모드로 설정
    }
}

WINDOW_NAME = "Smart Safety System - Realtime Test"


def main():
    """메인 테스트 함수"""
    logger.info("실시간 통합 파이프라인 테스트를 시작합니다...")

    # 1. 모듈 초기화 (개선된 방식)
    try:
        input_adapter = InputAdapter(
            camera_index=CONFIG['input']['camera_index'],
            mock_mode=CONFIG['input']['mock_mode']
        )
        detector = Detector(CONFIG['detector'])

        # LogicFacade에 전체 설정을 전달하면, 내부에서 알아서 ControlFacade를 설정합니다.
        logic_facade = LogicFacade(config=CONFIG)

        logger.success("모든 모듈 초기화 완료.")
    except Exception as e:
        logger.error(f"모듈 초기화 중 심각한 오류 발생: {e}")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    logger.info(f"스트림 시작. [{WINDOW_NAME}] 창에서 'q' 키를 누르면 종료, 'm' 키로 컨베이어 모드를 전환합니다.")

    prev_time = 0
    conveyor_is_on = False

    while True:
        # 2. InputAdapter를 통해 입력 데이터 가져오기
        input_data = input_adapter.get_input()
        if input_data is None or input_data.get('raw_frame') is None:
            logger.warning("입력 스트림이 종료되었거나 프레임을 가져올 수 없습니다.")
            break

        raw_frame = input_data['raw_frame']
        sensor_data = input_data['sensor_data']

        # 3. 시뮬레이션을 위해 컨베이어 작동 상태를 수동으로 주입
        sensor_data['sensors']['conveyor_operating'] = {'value': 1 if conveyor_is_on else 0}

        # 4. Detector를 사용하여 탐지 수행
        detection_result = detector.detect(raw_frame)

        # 5. LogicFacade를 사용하여 위험 평가 및 제어 액션 결정/실행
        actions = logic_facade.process(
            detection_result=detection_result,
            sensor_data=sensor_data
        )

        # 6. 탐지 결과를 프레임에 시각화
        display_frame = detector.draw_detections(raw_frame, detection_result)

        # 7. 추가 정보(FPS, 시스템 상태)를 프레임에 오버레이
        current_time = time.time()
        if prev_time > 0:
            fps = 1 / (current_time - prev_time)
            cv2.putText(display_frame, f"FPS: {fps:.2f}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        prev_time = current_time

        mode_text = "Mode: OPERATING" if conveyor_is_on else "Mode: STOPPED"
        risk_level = logic_facade.risk_evaluator.evaluate(detection_result, sensor_data)["risk_level"]
        cv2.putText(display_frame, mode_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(display_frame, f"Risk Level: {risk_level.upper()}", (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 165, 255), 2)

        action_summary = ", ".join([a['type'] for a in actions]) if actions else "No Actions"
        cv2.putText(display_frame, f"Actions: {action_summary}", (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 1)

        # 8. 화면에 결과 프레임 출력
        cv2.imshow(WINDOW_NAME, display_frame)

        # 9. 키 입력 처리
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            logger.info("'q' 키가 입력되어 테스트를 종료합니다.")
            break
        elif key == ord('m'):
            conveyor_is_on = not conveyor_is_on
            logger.info(f"컨베이어 모드 변경 -> {'작동 중' if conveyor_is_on else '작동 멈춤'}")

    # 10. 자원 해제
    input_adapter.release()
    cv2.destroyAllWindows()
    logger.info("테스트 종료. 모든 자원을 해제했습니다.")


if __name__ == '__main__':
    main()