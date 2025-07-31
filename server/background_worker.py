import asyncio
import cv2
import time
import sys
from pathlib import Path
from loguru import logger
from fastapi import FastAPI

# --------------------------------------------------------------------------
# 시스템 경로 설정 및 모듈 임포트
# --------------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent.parent))

from input_adapter.input_facade import InputAdapter

# 전역 변수 및 상태 제어 함수는 모두 제거되었습니다.
# 스트리밍을 위한 최신 프레임은 app.state를 통해 관리하는 것이 더 안전하지만,
# 여기서는 단순성을 위해 임시로 전역 변수를 유지합니다.
latest_frame = None

def get_latest_frame():
    """UI 스트리밍을 위해 최신 프레임을 반환합니다."""
    return latest_frame

# --------------------------------------------------------------------------
# 핵심 안전 시스템 워커 함수
# --------------------------------------------------------------------------
def run_safety_system(app: FastAPI):
    """
    실시간 영상 처리 및 안전 로직을 수행하는 메인 루프 (중앙 조정자).
    FastAPI의 lifespan에서 별도 스레드로 실행됩니다.
    `state_manager.is_active()` 상태에 따라 로직 수행 여부를 결정합니다.
    """
    global latest_frame
    logger.info("백그라운드 안전 시스템 워커 스레드를 시작합니다...")

    # app.state에서 중앙 관리 객체들을 가져옵니다.
    try:
        state_manager = app.state.state_manager
        logic_facade = app.state.logic_facade
        control_facade = app.state.control_facade
        detector = app.state.detector
        db_service = app.state.db_service
        alert_service = app.state.alert_service
        loop = app.state.loop
    except AttributeError as e:
        logger.critical(f"app.state에서 객체를 가져오는 데 실패했습니다: {e}. Lifespan 초기화가 실패했을 수 있습니다.")
        return

    try:
        input_adapter = InputAdapter(camera_index=0, mock_mode=False)
        logger.success("InputAdapter 초기화 완료.")
    except Exception as e:
        logger.error(f"InputAdapter 초기화 중 심각한 오류 발생: {e}")
        return

    # 최초 실행 시 컨베이어 전원을 끄고 시스템 상태를 기록합니다.
    logger.info("안전 초기화: 컨베이어 전원을 OFF 상태로 시작합니다.")
    control_facade.execute_actions([{"type": "POWER_OFF"}])
    db_service.log_event({
        "event_type": "LOG_SYSTEM_INITIALIZED", 
        "details": {"message": "System worker started, conveyor forced OFF."}
    })

    while True:
        try:
            # 1. 영상 프레임 및 센서 데이터 획득 (항상 실행)
            input_data = input_adapter.get_input()
            if input_data is None or input_data.get('raw_frame') is None:
                logger.warning("입력 스트림으로부터 프레임을 가져올 수 없습니다. 1초 후 재시도...")
                time.sleep(1)
                continue
            
            raw_frame = input_data['raw_frame']
            display_frame = raw_frame.copy()

            # 2. 시스템 활성화 상태일 때만 안전 로직 및 시각화 수행
            if state_manager.is_active():
                sensor_data = input_data['sensor_data']
                current_mode = state_manager.get_mode()
                conveyor_status = control_facade.get_power_status()['conveyor_is_on']

                # 객체 탐지
                detection_result = detector.detect(raw_frame)

                # 로직 처리 (두뇌에게 판단 요청)
                actions = logic_facade.process(
                    detection_result=detection_result,
                    sensor_data=sensor_data,
                    current_mode=current_mode,
                    current_conveyor_status=conveyor_status
                )

                # 액션 실행 (조정자가 실행 분배)
                control_actions = []
                for action in actions:
                    action_type = action.get("type")
                    if action_type in ['POWER_ON', 'POWER_OFF', 'REDUCE_SPEED_50']:
                        control_actions.append(action)
                    
                    elif action_type and action_type.startswith('LOG_'):
                        event_data = {
                            "event_type": action_type,
                            "details": action.get("details", {}),
                            "risk_level": logic_facade.last_risk_analysis.get("risk_level", "N/A")
                        }
                        # DB 로깅은 비동기일 수 있으므로 스레드-세이프하게 호출
                        db_service.log_event(event_data)
                    
                    elif action_type == 'NOTIFY_UI':
                        # UI 알림은 비동기 함수이므로, 스레드 안전하게 이벤트 루프를 통해 실행
                        coro = alert_service.connection_manager.broadcast(action.get("details", {}))
                        asyncio.run_coroutine_threadsafe(coro, loop)

                if control_actions:
                    control_facade.execute_actions(control_actions)

                # 시각화 및 스트리밍 프레임 업데이트
                display_frame = detector.draw_detections(raw_frame, detection_result)
                
                mode_text = f"Mode: {current_mode}"
                final_conveyor_status = control_facade.get_power_status()['conveyor_is_on']
                status_text = "Status: RUNNING" if final_conveyor_status else "Status: STOPPED"
                risk_level = logic_facade.last_risk_analysis.get("risk_level", "N/A")

                cv2.putText(display_frame, mode_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(display_frame, status_text, (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(display_frame, f"Risk: {risk_level.upper()}", (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            
            else:
                # 시스템이 비활성화 상태일 때 대기하며 화면에 상태 표시
                cv2.putText(display_frame, "SYSTEM INACTIVE", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                time.sleep(0.5) # CPU 사용량 감소를 위한 대기

            # 3. 최신 프레임을 전역 변수에 업데이트 (항상 실행)
            latest_frame = display_frame.copy()

        except Exception as e:
            logger.error(f"백그라운드 워커 루프에서 예외 발생: {e}", exc_info=True)
            time.sleep(5)

    input_adapter.release()
    logger.info("백그라운드 안전 시스템 워커가 종료되었습니다.")