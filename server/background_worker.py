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
async def run_safety_system(app: FastAPI):
    """
    실시간 영상 처리 및 안전 로직을 수행하는 메인 루프 (중앙 조정자).
    FastAPI의 lifespan에서 비동기 태스크로 실행됩니다.
    `state_manager.is_active()` 상태에 따라 로직 수행 여부를 결정합니다.
    """
    global latest_frame
    logger.info("비동기 안전 시스템 워커를 시작합니다...")

    # app.state에서 중앙 관리 객체들을 가져옵니다.
    try:
        state_manager = app.state.state_manager
        logic_facade = app.state.logic_facade
        control_facade = app.state.control_facade
        detector = app.state.detector
        db_service = app.state.db_service
        websocket_service = app.state.websocket_service
        loop = app.state.loop
    except AttributeError as e:
        logger.critical(f"app.state에서 객체를 가져오는 데 실패했습니다: {e}. Lifespan 초기화가 실패했을 수 있습니다.")
        return

    # lifespan에서 생성된 InputAdapter 인스턴스를 사용합니다.
    input_adapter = app.state.input_adapter

    # 최초 실행 시 컨베이어 전원을 끄고 시스템 상태를 기록합니다.
    logger.info("안전 초기화: 컨베이어 전원을 OFF 상태로 시작합니다.")
    control_facade.execute_actions([{"type": "POWER_OFF"}])
    db_service.log_event({
        "event_type": "LOG_SYSTEM_INITIALIZED", 
        "details": {"message": "System worker started, conveyor forced OFF."}
    })

    while True:
        try:
            # 1. (신규) 아두이노의 자율 제어 이벤트 확인 및 처리
            autonomous_events = input_adapter.get_status_events()
            if autonomous_events:
                logger.info(f"[Worker] 수신된 자율 제어 이벤트: {autonomous_events}")

            # 2. 영상 프레임 획득
            raw_frame = input_adapter.get_frame()
            if raw_frame is None:
                logger.warning("입력 스트림으로부터 프레임을 가져올 수 없습니다. 1초 후 재시도...")
                await asyncio.sleep(1)
                continue
            
            display_frame = raw_frame.copy()

            # 3. 시스템 활성화 상태일 때만 안전 로직 및 시각화 수행
            if state_manager.is_active():
                # 센서 데이터는 필요할 때만 별도로 획득
                sensor_data = input_adapter.get_sensor_data()
                current_status = state_manager.get_status()
                current_mode = current_status.get("operation_mode")
                conveyor_is_on = current_status.get("conveyor_is_on", False)
                conveyor_speed = current_status.get("conveyor_speed", 100)

                # 객체 탐지
                detection_result = detector.detect(raw_frame)
                app.state.latest_detection_result = detection_result

                # 로직 처리 (두뇌에게 판단 요청)
                actions = logic_facade.process(
                    detection_result=detection_result,
                    sensor_data=sensor_data,
                    current_mode=current_mode,
                    current_conveyor_status=conveyor_is_on,
                    current_conveyor_speed=conveyor_speed,
                    autonomous_events=autonomous_events
                )

                # 액션 실행 (조정자가 실행 분배)
                control_actions = []
                for action in actions:
                    action_type = action.get("type")
                    if action_type in ['POWER_ON', 'POWER_OFF', 'REDUCE_SPEED_50', 'RESUME_FULL_SPEED'] or action_type.startswith('TRIGGER_ALARM_'):
                        control_actions.append(action)
                    
                    elif action_type and action_type.startswith('LOG_'):
                        risk_factors = logic_facade.last_risk_analysis.get("risk_factors", [])

                        # 로그 레벨과 설명을 결정
                        log_risk_level = "INFO"  # 기본값
                        description = "System is operating normally."

                        # 가장 중요한 위험 사실 하나를 찾아 설명과 레벨을 설정
                        if any(f["type"] == "POSTURE_FALLING" for f in risk_factors):
                            log_risk_level = "CRITICAL"
                            description = "A person falling has been detected."
                        elif any(f["type"] == "SENSOR_ALERT" for f in risk_factors):
                            log_risk_level = "CRITICAL"
                            sensor_type = next((f.get("sensor_type") for f in risk_factors if f["type"] == "SENSOR_ALERT"), "unknown")
                            description = f"An emergency signal from sensor '{sensor_type}' has been detected."
                        elif any(f["type"] == "ZONE_INTRUSION" for f in risk_factors):
                            log_risk_level = "WARNING"
                            intrusion_details = next((f.get("details") for f in risk_factors if f["type"] == "ZONE_INTRUSION"), [])
                            zone_names = ", ".join(list(set(alert["zone_name"] for alert in intrusion_details)))
                            description = f"Person detected in danger zone(s): {zone_names}."
                        elif any(f["type"] == "POSTURE_CROUCHING" for f in risk_factors):
                            log_risk_level = "NOTICE"
                            description = "A person in a crouching pose has been detected."

                        event_data = {
                            "event_type": action_type,
                            "details": {"description": description},
                            "log_risk_level": log_risk_level
                        }
                        db_service.log_event(event_data)
                    
                    elif action_type == 'NOTIFY_UI':
                        asyncio.run_coroutine_threadsafe(
                            websocket_service.broadcast_to_channel('alerts', action.get("details", {})),
                            loop
                        )

                if control_actions:
                    control_facade.execute_actions(control_actions)

                # 시각화 및 스트리밍 프레임 업데이트
                display_frame = detector.draw_detections(raw_frame, detection_result)
                
                # 최종 상태를 다시 가져와서 화면에 표시
                final_status = state_manager.get_status()
                mode_text = f"Mode: {final_status.get('operation_mode', 'N/A')}"

                # 속도와 전원 상태를 조합하여 더 상세한 상태 텍스트 생성
                is_on = final_status.get('conveyor_is_on', False)
                speed = final_status.get('conveyor_speed', 100)

                if not is_on:
                    status_text = "Status: STOPPED"
                elif speed < 100:
                    status_text = f"Status: SLOWDOWN ({speed}%)"
                else:
                    status_text = "Status: RUNNING"

                risk_factors = logic_facade.last_risk_analysis.get("risk_factors", [])
                risk_text = "Risk: DETECTED" if risk_factors else "Risk: SAFE"
                risk_color = (0, 0, 255) if risk_factors else (0, 255, 0)

                cv2.putText(display_frame, mode_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(display_frame, status_text, (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(display_frame, risk_text, (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, risk_color, 2)
            
            else:
                # 시스템이 비활성화 상태일 때 대기하며 화면에 상태 표시
                cv2.putText(display_frame, "SYSTEM INACTIVE", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                await asyncio.sleep(0.5)

            # 3. 최신 프레임을 전역 변수에 업데이트 (항상 실행)
            latest_frame = display_frame.copy()
            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"백그라운드 워커 루프에서 예외 발생: {e}", exc_info=True)
            await asyncio.sleep(5)

    input_adapter.release()
    logger.info("비동기 안전 시스템 워커가 종료되었습니다.")
