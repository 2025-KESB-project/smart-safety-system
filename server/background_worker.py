import asyncio
import cv2
import time
import sys
import os
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------------------------------------------------------
# 시스템 경로 설정 및 모듈 임포트
# --------------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent.parent))

from input_adapter.input_facade import InputAdapter
from server.services.db_service import DBService

# 스트리밍을 위한 최신 프레임은 app.state를 통해 관리합니다.
# 전역 변수는 제거되었습니다.
def get_latest_frame(app: FastAPI):
    """UI 스트리밍을 위해 app.state에서 최신 프레임을 반환합니다."""
    return getattr(app.state, 'latest_frame', None)

# --------------------------------------------------------------------------
# 핵심 안전 시스템 워커 함수
# --------------------------------------------------------------------------
async def run_safety_system(app: FastAPI):
    """
    실시간 영상 처리 및 안전 로직을 수행하는 메인 루프 (중앙 조정자).
    FastAPI의 lifespan에서 비동기 태스크로 실행됩니다.
    `state_manager.is_active()` 상태에 따라 로직 수행 여부를 결정합니다.
    """
    app.state.latest_frame = None
    logger.info("비동기 안전 시스템 워커를 시작합니다...")

    try:
        # 1. app.state에서 필요한 서비스들을 가져옵니다.
        state_manager = app.state.state_manager
        logic_facade = app.state.logic_facade
        control_facade = app.state.control_facade
        detector = app.state.detector
        db_service = app.state.db_service # app.py에서 초기화된 DB 서비스 사용
        loop = app.state.loop # 이벤트 루프 가져오기

    except AttributeError as e:
        logger.critical(f"app.state에서 객체를 가져오는 데 실패했습니다: {e}. Lifespan 초기화가 실패했을 수 있습니다.")
        return

    # 2. InputAdapter 초기화 (카메라/센서)
    try:
        logger.info("InputAdapter 초기화를 시작합니다...")
        input_adapter = InputAdapter(camera_index=3, mock_mode=False)
        logger.success("InputAdapter 초기화 완료.")
    except Exception as e:
        logger.error(f"InputAdapter 초기화 중 심각한 오류 발생: {e}", exc_info=True)
        return

    # 최초 실행 시 컨베이어 전원을 끄고 시스템 상태를 기록합니다.
    logger.info("안전 초기화: 컨베이어 전원을 OFF 상태로 시작합니다.")
    await control_facade.execute_actions([{"type": "POWER_OFF"}])
    await db_service.log_event({
        "event_type": "LOG_SYSTEM_INITIALIZED", 
        "details": {"message": "System worker started, conveyor forced OFF."}
    })

    while True:
        try:
            # 1. 영상 프레임 및 센서 데이터 획득 (항상 실행)
            logger.debug("영상 프레임 및 센서 데이터 획득 시도...")
            input_data = input_adapter.get_input()
            if input_data is None or input_data.get('raw_frame') is None:
                logger.warning("입력 스트림으로부터 프레임을 가져올 수 없습니다. 1초 후 재시도...")
                await asyncio.sleep(1)
                continue
            
            logger.debug("영상 프레임 획득 성공.")
            raw_frame = input_data['raw_frame']
            display_frame = raw_frame.copy()

            # 2. 시스템 활성화 상태일 때만 안전 로직 및 시각화 수행
            if state_manager.is_active():
                logger.debug("시스템 활성화 상태. 안전 로직 수행...")
                # ... (이하 로직은 동일) ...
                current_status = state_manager.get_status()
                current_mode = current_status.get("operation_mode")
                conveyor_is_on = current_status.get("conveyor_is_on", False)
                conveyor_speed = current_status.get("conveyor_speed", 100)
                sensor_data = input_data['sensor_data']

                # CPU를 많이 사용하는 모델 추론 작업을 별도의 스레드에서 실행하여 이벤트 루프 블로킹 방지
                detection_result = await loop.run_in_executor(None, detector.detect, raw_frame)
                app.state.latest_detection_result = detection_result

                actions = logic_facade.process(
                    detection_result=detection_result,
                    sensor_data=sensor_data,
                    current_mode=current_mode,
                    current_conveyor_status=conveyor_is_on,
                    current_conveyor_speed=conveyor_speed
                )

                control_actions = []
                for action in actions:
                    action_type = action.get("type")
                    if action_type in ['POWER_ON', 'POWER_OFF', 'REDUCE_SPEED_50', 'RESUME_FULL_SPEED'] or action_type.startswith('TRIGGER_ALARM_'):
                        control_actions.append(action)
                    
                    elif action_type and action_type.startswith('LOG_'):
                        risk_factors = logic_facade.last_risk_analysis.get("risk_factors", [])
                        log_risk_level = "INFO"
                        description = "System is operating normally."
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
                            "risk_level": log_risk_level
                        }
                        await db_service.log_event(event_data)
                    
                    

                if control_actions:
                    await control_facade.execute_actions(control_actions)

                display_frame = detector.draw_detections(raw_frame, detection_result)
                
                final_status = state_manager.get_status()
                mode_text = f"Mode: {final_status.get('operation_mode', 'N/A')}"
                
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
                logger.debug("시스템 비활성화 상태. 안전 로직 건너뜀.")
                cv2.putText(display_frame, "SYSTEM INACTIVE", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                await asyncio.sleep(0.5)

            app.state.latest_frame = display_frame.copy()
            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"백그라운드 워커 루프에서 예외 발생: {e}", exc_info=True)
            await asyncio.sleep(5)

    input_adapter.release()
    logger.info("비동기 안전 시스템 워커가 종료되었습니다.")