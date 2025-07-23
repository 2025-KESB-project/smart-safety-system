# test_realtime_pipeline.py

import cv2
import time
from pathlib import Path
import sys
from typing import Dict, Any

# --------------------------------------------------------------------------
# 로깅 설정 (가장 먼저 수행)
# --------------------------------------------------------------------------
from loguru import logger

# 기본 핸들러 제거 및 새로운 핸들러 설정
logger.remove()
# test.py (__main__)의 로그만 INFO 레벨부터 허용하고, 그 외 모든 모듈은 WARNING 레벨부터 허용
logger.add(
    sys.stderr,
    level="INFO",
    filter=lambda record: record["name"] == "__main__" or record["level"].no >= logger.level("WARNING").no,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
)

# --------------------------------------------------------------------------
# 시스템 경로 설정 및 모듈 임포트
# --------------------------------------------------------------------------
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from input_adapter.input_facade import InputAdapter
    from detect.detect_facade import Detector
    from logic.logic_facade import LogicFacade
    from server.service_facade import ServiceFacade # ServiceFacade 임포트
    from config.config import Config
    logger.info("모듈 경로 설정 완료.")
except ImportError as e:
    logger.error(f"모듈을 임포트할 수 없습니다. 스크립트를 프로젝트 루트에서 실행하고 있는지 확인하세요. 오류: {e}")
    sys.exit(1)



# --------------------------------------------------------------------------
# 테스트 설정
# --------------------------------------------------------------------------
CONFIG = {
    'input': {
        'camera_index': 3,
        'mock_mode': False
    },
    'detector': {
        'person_detector': {'model_path': 'yolov8n.pt'},
        'pose_detector': {'model_path': 'yolov8n-pose.pt'},
        'danger_zone_mapper': {'zone_config_path': 'danger_zones.json'}
    },
    'control': {
        'mock_mode': True
    },
    'service': {
        'db_service': {
            'firebase_credentials_path': str(Path(__file__).parent.parent / "config" / "firebase_credential.json"),
            'collection_name': 'event_logs' # Firestore 컬렉션 이름
        }
    }
}

WINDOW_NAME = "Smart Safety System - Realtime Test"


def main():
    logger.info("실시간 통합 파이프라인 테스트를 시작합니다...")

    try:
        # ServiceFacade 초기화
        service_facade = ServiceFacade(config=CONFIG.get('service', {}))

        input_adapter = InputAdapter(
            camera_index=CONFIG['input']['camera_index'],
            mock_mode=CONFIG['input']['mock_mode']
        )
        detector = Detector(CONFIG['detector'])
        # LogicFacade 초기화 시 ServiceFacade를 전달합니다.
        logic_facade = LogicFacade(config=CONFIG, service_facade=service_facade)
        logger.success("모든 모듈 초기화 완료.")
    except Exception as e:
        logger.error(f"모듈 초기화 중 심각한 오류 발생: {e}")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    logger.info(f"스트림 시작. [{WINDOW_NAME}] 창에서 'q' 키를 누르면 종료, 'm' 키로 컨베이어 모드를 전환합니다.")

    prev_time = 0
    conveyor_is_on = False
    # 이전 상태를 저장하는 변수들
    previous_risk_level = None
    previous_action_types = []

    while True:
        input_data = input_adapter.get_input()
        if input_data is None or input_data.get('raw_frame') is None:
            logger.warning("입력 스트림이 종료되었거나 프레임을 가져올 수 없습니다.")
            break

        raw_frame = input_data['raw_frame']
        sensor_data = input_data['sensor_data']
        sensor_data['sensors']['conveyor_operating'] = {'value': 1 if conveyor_is_on else 0}

        detection_result = detector.detect(raw_frame)
        actions = logic_facade.process(detection_result=detection_result, sensor_data=sensor_data)
        
        # 현재 상태 정의
        risk_analysis = logic_facade.last_risk_analysis
        
        # --- Firestore 이벤트 로깅 ---
        # RuleEngine에서 반환된 actions 중 LOG 타입 액션을 DB에 기록
        for action in actions:
            if action.get("type", "").startswith("LOG_"):
                service_facade.db_service.log_event(
                    event_type=action["type"],
                    risk_level=risk_analysis.get("risk_level", "unknown"),
                    details=action.get("details", {})
                )

        current_risk_level = risk_analysis.get("risk_level", "unknown")
        current_action_types = sorted([a['type'] for a in actions])

        # "의미 있는" 상태가 변경되었을 때만 로그 출력
        if current_risk_level != previous_risk_level or current_action_types != previous_action_types:
            logger.info(f"상태 변경 감지: [위험 수준: {current_risk_level}] [모드: {'작동' if conveyor_is_on else '멈춤'}]")
            if actions:
                logger.info(f"  -> 수행 조치: {', '.join(current_action_types)}")
            else:
                logger.info("  -> 수행 조치 없음")
            
            # 현재 상태를 이전 상태로 업데이트
            previous_risk_level = current_risk_level
            previous_action_types = current_action_types

        # --- 시각화 부분 ---
        display_frame = detector.draw_detections(raw_frame, detection_result)
        
        current_time = time.time()
        if prev_time > 0:
            fps = 1 / (current_time - prev_time)
            cv2.putText(display_frame, f"FPS: {fps:.2f}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        prev_time = current_time

        mode_text = "Mode: OPERATING" if conveyor_is_on else "Mode: STOPPED"
        cv2.putText(display_frame, mode_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(display_frame, f"Risk Level: {current_risk_level.upper()}", (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        
        action_summary_display = ", ".join(current_action_types) if actions else "No Actions"
        cv2.putText(display_frame, f"Actions: {action_summary_display}", (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow(WINDOW_NAME, display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            logger.info("'q' 키가 입력되어 테스트를 종료합니다.")
            break
        elif key == ord('m'):
            conveyor_is_on = not conveyor_is_on
            logger.info(f"컨베이어 모드 변경 -> {'작동 중' if conveyor_is_on else '작동 멈춤'}")

    input_adapter.release()
    cv2.destroyAllWindows()
    logger.info("테스트 종료. 모든 자원을 해제했습니다.")

if __name__ == '__main__':
    main()
