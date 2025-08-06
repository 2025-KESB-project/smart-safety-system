import asyncio
import cv2
import time
import sys
from pathlib import Path
from loguru import logger
from multiprocessing import Queue
import torch
import threading
from typing import Dict, Any

# --------------------------------------------------------------------------
# 시스템 경로 설정 및 모듈 임포트
# --------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# TODO config 설정
from config.config import get_config
from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from control.control_facade import ControlFacade
from server.state_manager import SystemStateManager
from server.services.zone_service import ZoneService

# --------------------------------------------------------------------------
# 컴포넌트 초기화 함수
# --------------------------------------------------------------------------
def initialize_components(config: Dict[str, Any]):
    """
    비전 워커에 필요한 모든 핵심 컴포넌트를 초기화하고 반환합니다.
    """
    logger.info("비전 워커 컴포넌트 초기화를 시작합니다...")

    input_adapter = InputAdapter(config["input"])
    # ZoneService는 이제 Vision Worker에서 직접 사용되지 않습니다.
    # detector = Detector(config["detection"], zone_service=zone_service)
    detector = Detector(config["detection"])
    
    control_config = config.get("control", {})
    control_facade = ControlFacade(
        mock_mode=control_config.get("mock_mode", True),
        serial_port=control_config.get("serial_port"),
        baud_rate=control_config.get("baud_rate", 9600)
    )
    
    state_manager = SystemStateManager()
    logic_facade = LogicFacade(config.get("logic", {}))

    logger.info("모든 비전 워커 컴포넌트가 성공적으로 초기화되었습니다.")
    
    return input_adapter, detector, control_facade, state_manager, logic_facade

# --------------------------------------------------------------------------
# 핵심 안전 시스템 워커 함수
# --------------------------------------------------------------------------
async def run_safety_system(command_queue: Queue, log_queue: Queue, frame_queue: Queue):
    """
    실시간 영상 처리 및 안전 로직을 수행하는 메인 루프.
    """
    logger.info("독립 비전 워커 프로세스를 시작합니다...")

    config = get_config()
    try:
        input_adapter, detector, control_facade, state_manager, logic_facade = initialize_components(config)
    except Exception as e:
        logger.critical(f"컴포넌트 초기화 중 심각한 오류 발생: {e}", exc_info=True)
        log_queue.put({"type": "LOG", "data": {"event_type": "LOG_SYSTEM_ERROR", "details": {"message": f"Worker initialization failed: {e}"}, "log_level": "CRITICAL"}})
        return

    # 최초 실행 시 컨베이어 전원을 끄고 시스템 상태를 기록합니다.
    logger.info("안전 초기화: 컨베이어 전원을 OFF 상태로 시작합니다.")
    await control_facade.execute_actions([{"type": "POWER_OFF", "details": {"reason": "Worker initialization"}}])
    log_queue.put({
        "type": "LOG",
        "data": {
            "event_type": "LOG_SYSTEM_INITIALIZED", 
            "details": {"message": "System worker started, conveyor forced OFF."},
            "log_level": "SUCCESS"
        }
    })

    while True:
        try:
            # 1. FastAPI 서버로부터 명령 수신 및 처리
            if not command_queue.empty():
                command = command_queue.get_nowait()
                logger.info(f"FastAPI 서버로부터 명령 수신: {command}")
                cmd_type = command.get("command")
                if cmd_type == "START_AUTOMATIC":
                    state_manager.start_automatic_mode()
                elif cmd_type == "START_MAINTENANCE":
                    state_manager.start_maintenance_mode()
                elif cmd_type == "STOP":
                    state_manager.stop_system_globally()
                    # 프로그램 종료 로직 추가
                    logger.info("STOP 명령 수신, 워커를 종료합니다.")
                    break
                elif cmd_type == "UPDATE_ZONES":
                    zones = command.get("data", [])
                    detector.danger_zone_mapper.update_zones_from_data(zones)
                    logger.info(f"Vision Worker의 Zone 정보가 {len(zones)}개로 업데이트되었습니다.")

            # 2. 영상 프레임 획득
            raw_frame = input_adapter.get_frame()
            if raw_frame is None:
                await asyncio.sleep(0.1)
                continue
            
            display_frame = raw_frame.copy()
            loop = asyncio.get_running_loop()

            # 3. 시스템 활성화 상태일 때만 안전 로직 및 시각화 수행
            if state_manager.is_active():
                sensor_data = input_adapter.get_sensor_data()
                
                # 객체 탐지 (CPU 집약적 작업을 별도 스레드에서 실행하여 이벤트 루프 블로킹 방지)
                detection_result = await loop.run_in_executor(None, detector.detect, raw_frame)

                # 논리적 상태는 메인 루프에서 직접 가져옴
                current_status = state_manager.get_status()
                current_mode = current_status.get("operation_mode")

                # 물리적 상태는 ControlFacade를 통해 동기적으로 가져옴 (캐시된 상태)
                physical_status = control_facade.get_all_statuses()
                conveyor_is_on = physical_status.get("conveyor_is_on", False)
                conveyor_speed = physical_status.get("conveyor_speed", 100)

                # 로직 처리
                actions = logic_facade.process(
                    detection_result=detection_result,
                    sensor_data=sensor_data,
                    current_mode=current_mode,
                    current_conveyor_status=conveyor_is_on,
                    current_conveyor_speed=conveyor_speed
                )

                # 액션 실행
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
                        log_queue.put({"type": "LOG", "data": event_data})
                    
                    elif action_type == 'NOTIFY_UI':
                        log_queue.put({"type": "ALERT", "data": action.get("details", {})})

                if control_actions:
                    await control_facade.execute_actions(control_actions)

                # 시각화 및 스트리밍 프레임 업데이트
                display_frame = detector.draw_detections(raw_frame, detection_result)
                
                # 최종 상태를 다시 가져와서 화면에 표시
                logical_status = state_manager.get_status()
                physical_status = control_facade.get_all_statuses()
                final_status = {**logical_status, **physical_status}

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
                cv2.putText(display_frame, "SYSTEM INACTIVE", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                await asyncio.sleep(0.5)

            # 4. 처리된 프레임을 FastAPI 서버로 전송
            if not frame_queue.full():
                # 프레임을 JPEG로 인코딩하여 바이트로 변환
                _, encoded_frame = cv2.imencode('.jpg', display_frame)
                frame_queue.put_nowait(encoded_frame.tobytes())
            
            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"비전 워커 루프에서 예외 발생: {e}", exc_info=True)
            log_queue.put({"type": "LOG", "data": {"event_type": "LOG_SYSTEM_ERROR", "details": {"message": str(e)}, "log_level": "ERROR"}})
            await asyncio.sleep(5)

    input_adapter.release()
    logger.info("비전 워커 프로세스가 종료되었습니다.")

# --------------------------------------------------------------------------
# 워커 실행기
# --------------------------------------------------------------------------
def run_worker_process(command_q: Queue, log_q: Queue, frame_q: Queue):
    """
    asyncio 이벤트 루프를 설정하고 run_safety_system을 실행하는 진입점 함수.
    """
    try:
        asyncio.run(run_safety_system(command_q, log_q, frame_q))
    except KeyboardInterrupt:
        logger.info("비전 워커가 사용자에 의해 중지되었습니다.")

if __name__ == '__main__':
    # 이 파일을 직접 실행할 때 테스트를 위한 코드
    logger.info("Vision worker를 단독으로 실행합니다 (테스트 모드)")
    cmd_q = Queue()
    log_q = Queue()
    frame_q = Queue(maxsize=2)

    # 테스트를 위해 15초 후에 정지 명령 전송
    def send_stop_command():
        time.sleep(15)
        cmd_q.put({"command": "STOP"})
        logger.info("테스트: STOP 명령 전송")

    
    threading.Thread(target=send_stop_command, daemon=True).start()

    # 로그 큐 모니터링
    def log_monitor():
        while True:
            if not log_q.empty():
                print(f"[LOG_QUEUE]: {log_q.get()}")
            time.sleep(0.1)
    
    threading.Thread(target=log_monitor, daemon=True).start()

    run_worker_process(cmd_q, log_q, frame_q)
