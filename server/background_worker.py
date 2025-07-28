
import asyncio
import cv2
import time
import sys
from pathlib import Path
from loguru import logger

# --------------------------------------------------------------------------
# 시스템 경로 설정 및 모듈 임포트
# --------------------------------------------------------------------------
# 이 파일이 server 디렉토리에 있으므로, 프로젝트 루트는 parent.parent가 됩니다.
sys.path.append(str(Path(__file__).parent.parent))

from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from server.service_facade import ServiceFacade

# --------------------------------------------------------------------------
# 전역 변수 및 상태 관리
# --------------------------------------------------------------------------
# 이 변수들은 FastAPI의 다른 부분(예: 스트리밍)에서 접근해야 할 수 있습니다.
# app.state를 통해 관리하는 것이 더 나은 방법일 수 있습니다.
latest_frame = None
latest_detection_result = None
conveyor_is_on = False # 초기 상태는 멈춤

def get_latest_frame():
    """다른 모듈에서 처리된 최신 프레임을 가져오기 위한 함수"""
    return latest_frame

def start_conveyor():
    """컨베이어를 작동시킵니다."""
    global conveyor_is_on
    if not conveyor_is_on:
        conveyor_is_on = True
        logger.info("컨베이어 모드 변경 -> 작동 시작")
    return conveyor_is_on

def stop_conveyor():
    """컨베이어를 정지시킵니다."""
    global conveyor_is_on
    if conveyor_is_on:
        conveyor_is_on = False
        logger.info("컨베이어 모드 변경 -> 작동 멈춤")
    return conveyor_is_on

def get_conveyor_status():
    """현재 컨베이어 작동 상태를 반환합니다."""
    return conveyor_is_on

# --------------------------------------------------------------------------
# 핵심 안전 시스템 워커 함수
# --------------------------------------------------------------------------
def run_safety_system(config: dict, service_facade: ServiceFacade, detector: Detector, logic_facade: LogicFacade, loop: asyncio.AbstractEventLoop):
    """
    실시간 영상 처리 및 안전 로직을 수행하는 메인 루프.
    FastAPI의 백그라운드 스레드에서 실행됩니다.
    """
    global latest_frame, latest_detection_result, conveyor_is_on
    logger.info("백그라운드 안전 시스템 워커를 시작합니다...")

    try:
        input_adapter = InputAdapter(
            camera_index=config['input']['camera_index'],
            mock_mode=config['input']['mock_mode']
        )
        logger.success("InputAdapter 초기화 완료.")
    except Exception as e:
        logger.error(f"InputAdapter 초기화 중 심각한 오류 발생: {e}")
        return

    previous_risk_level = None
    previous_action_types = []

    while True:
        try:
            input_data = input_adapter.get_input()
            if input_data is None or input_data.get('raw_frame') is None:
                logger.warning("입력 스트림이 종료되었거나 프레임을 가져올 수 없습니다. 1초 후 재시도...")
                time.sleep(1)
                continue

            raw_frame = input_data['raw_frame']
            sensor_data = input_data['sensor_data']
            # 현재 컨베이어 상태를 센서 데이터에 주입
            sensor_data['sensors']['conveyor_operating'] = {'value': 1 if conveyor_is_on else 0}

            # 탐지 및 로직 처리
            detection_result = detector.detect(raw_frame)
            actions = logic_facade.process(detection_result=detection_result, sensor_data=sensor_data)
            
            risk_analysis = logic_facade.last_risk_analysis
            current_risk_level = risk_analysis.get("risk_level", "unknown")
            # set으로 변환하여 순서에 상관없이 비교하도록 개선
            current_action_types = set(a['type'] for a in actions)

            # --- 상태 변경 감지 및 로깅 ---
            if current_risk_level != previous_risk_level or current_action_types != previous_action_types:
                # 1. 터미널에 상태 변경 로그 출력
                action_names = sorted(list(current_action_types))
                logger.info(
                    f"상태 변경 감지: [위험 수준: {current_risk_level}] "
                    f"[모드: {'작동' if conveyor_is_on else '멈춤'}] -> "
                    f"조치: {', '.join(action_names) or '없음'}"
                )

                # 2. 상태가 변경되었을 때만 DB 로깅 및 UI 알림 실행
                for action in actions:
                    # DB 로깅
                    if action.get("type", "").startswith("LOG_"):
                        event_to_log = {
                            "event_type": action["type"],
                            "risk_level": risk_analysis.get("risk_level", "unknown"),
                            "details": action.get("details", {})
                        }
                        service_facade.db_service.log_event(event_to_log)
                    # UI 실시간 알림
                    if action.get("type") == "NOTIFY_UI":
                        coro = service_facade.alert_service.connection_manager.broadcast(action.get("details", {}))
                        asyncio.run_coroutine_threadsafe(coro, loop)
                
                # 3. 다음 비교를 위해 현재 상태를 이전 상태로 저장
                previous_risk_level = current_risk_level
                previous_action_types = current_action_types

            # 시각화 및 최신 프레임 업데이트
            display_frame = detector.draw_detections(raw_frame, detection_result)
            
            # UI에 표시할 정보 추가
            mode_text = "Mode: OPERATING" if conveyor_is_on else "Mode: STOPPED"
            cv2.putText(display_frame, mode_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(display_frame, f"Risk Level: {current_risk_level.upper()}", (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            action_summary_display = ", ".join(sorted(list(current_action_types))) if actions else "No Actions"
            cv2.putText(display_frame, f"Actions: {action_summary_display}", (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # 다른 모듈에서 사용할 수 있도록 최신 프레임과 탐지 결과 저장
            latest_frame = display_frame.copy()
            latest_detection_result = detection_result

        except Exception as e:
            logger.error(f"백그라운드 워커 루프에서 예외 발생: {e}", exc_info=True)
            time.sleep(5) # 오류 발생 시 잠시 대기 후 재시도

        # CPU 사용량을 줄이기 위해 아주 짧은 대기 시간 추가
        time.sleep(0.01)

    input_adapter.release()
    logger.info("백그라운드 안전 시스템 워커가 종료되었습니다.")
