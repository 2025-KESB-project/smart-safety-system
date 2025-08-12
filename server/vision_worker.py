import asyncio
import cv2
import time
import sys
from pathlib import Path

import numpy as np
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

from config.config import get_config
from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector
from logic.logic_facade import LogicFacade
from control.control_facade import ControlFacade
from server.state_manager import SystemStateManager
from server.services.zone_service import ZoneService
from server.models.websockets import StatusUpdateMessage
from core.serial_communicator import SerialCommunicator
from core.drawing_utils import put_text_korean

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
    communicator= SerialCommunicator(port=config["serial"]["port"], baud_rate=config["serial"]["baud_rate"], mock_mode=config["serial"]["mock_mode"])
    control_config = config.get("control", {})
    control_facade = ControlFacade(
        mock_mode=control_config.get("mock_mode", True),
        communicator=communicator
    )
    
    state_manager = SystemStateManager()
    logic_facade = LogicFacade(config.get("logic", {}))

    logger.info("모든 비전 워커 컴포넌트가 성공적으로 초기화되었습니다.")
    
    return input_adapter, detector, control_facade, state_manager, logic_facade, communicator

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
        input_adapter, detector, control_facade, state_manager, logic_facade, communicator = initialize_components(config)

        # --- 하드웨어 비상 정지 신호 리스너 설정 및 시작 ---
        communicator.set_lock_system_callback(state_manager.lock_system)
        communicator.set_is_locked_checker(state_manager.is_locked_status)
        communicator.start_listening()
        # ----------------------------------------------

        # --- 워밍업 단계 시작 ---
        logger.info("모델 워밍업을 시작합니다... (초기 지연을 줄이기 위한 과정)")
        warmup_start_time = time.perf_counter()
        # 실제 프레임과 유사한 크기의 가짜 이미지 생성 (예: 640x480)
        # 설정 파일에서 해상도를 가져오는 것이 더 좋지만, 여기서는 일반적인 크기를 사용합니다.
        h, w = config.get("input", {}).get("height", 480), config.get("input", {}).get("width", 640)
        fake_frame = np.zeros((h, w, 3), dtype=np.uint8)
        
        # 여러 시나리오를 가정하여 모델을 미리 호출
        # 1. 아무것도 없는 프레임
        detector.detect(fake_frame)
        # 2. 가짜 사람이 있는 프레임 (detector 내부의 pose_detector까지 활성화하기 위함)
        fake_persons = [{'bbox': [10, 10, 100, 200], 'confidence': 0.9, 'class_id': 0}]
        detector.pose_detector.detect(fake_frame, fake_persons)
        
        warmup_end_time = time.perf_counter()
        logger.info(f"모델 워밍업 완료. 소요 시간: {(warmup_end_time - warmup_start_time) * 1000:.2f}ms")
        # --- 워밍업 단계 종료 ---

    except Exception as e:
        logger.critical(f"컴포넌트 초기화 또는 워밍업 중 심각한 오류 발생: {e}", exc_info=True)
        log_queue.put({"type": "LOG", "data": {"event_type": "LOG_SYSTEM_ERROR", "details": {"message": f"Worker initialization or warmup failed: {e}"}, "log_level": "CRITICAL"}})
        return

    # 최초 실행 시 컨베이어 전원을 끄고 시스템 상태를 기록합니다.
    logger.info("안전 초기화: 컨베이어 전원을 OFF 상태로 시작합니다.")
    control_facade.execute_actions([{"type": "POWER_OFF", "details": {"reason": "Worker initialization"}}])
    log_queue.put({
        "type": "LOG",
        "data": {
            "event_type": "LOG_SYSTEM_INITIALIZED", 
            "details": {"message": "System worker started, conveyor forced OFF."},
            "log_level": "SUCCESS"
        }
    })

    last_status_message_data = None
    was_locked = False # 이전 프레임의 잠금 상태를 기억하는 변수
    TARGET_FPS = 15  # 목표 FPS를 15로 설정
    FRAME_DURATION = 1 / TARGET_FPS
    last_processed_time = time.perf_counter()

    while True:
        try:
            # 1. FastAPI 서버로부터 명령 수신 및 처리
            loop_start_time = time.perf_counter()

            if not command_queue.empty():
                command = command_queue.get_nowait()
                logger.info(f"FastAPI 서버로부터 명령 수신: {command}")
                cmd_type = command.get("command")
                
                # 모드 변경 커맨드 처리
                if cmd_type in ["START_AUTOMATIC", "START_MAINTENANCE", "STOP"]:
                    if cmd_type == "START_AUTOMATIC":
                        state_manager.start_automatic_mode()
                    elif cmd_type == "START_MAINTENANCE":
                        state_manager.start_maintenance_mode()
                    elif cmd_type == "STOP":
                        state_manager.stop_system_globally()
                        logger.info("STOP 명령 수신, 시스템은 정지 상태로 전환됩니다. 영상 스트림은 유지됩니다.")
                    
                    # 모드 변경 후 즉시 루프를 다시 시작하여 새로운 상태를 적용
                    continue
                
                elif cmd_type == "RESET": # 리셋 명령 처리
                    state_manager.reset_system()
                    logger.info("RESET 명령 수신, 시스템 잠금 상태를 해제합니다.")
                    # 만약을 위해 전원 차단 명령을 한 번 더 보냄
                    control_facade.execute_actions([{"type": "POWER_OFF", "details": {"reason": "System reset"}}])
                    
                    # --- 상태 변경 후 즉시 UI에 업데이트 전송 ---
                    try:
                        logical_status = state_manager.get_status()
                        physical_status = control_facade.get_all_statuses()
                        final_status = {**logical_status, **physical_status}
                        
                        # operation_mode가 None일 경우를 대비하여 기본값 설정
                        op_mode = final_status.get('operation_mode') or 'STOPPED'

                        status_message = StatusUpdateMessage(
                            operation_mode=op_mode,
                            conveyor_status="STOPPED", # 리셋 후에는 항상 정지 상태
                            conveyor_speed=0,
                            risk_level="SAFE", # 리셋 후에는 안전 상태
                            is_locked=False # 리셋되었으므로 False
                        )
                        status_message_data = status_message.model_dump()
                        log_queue.put({"type": "STATUS_UPDATE", "data": status_message_data})
                        last_status_message_data = status_message_data
                        logger.info("시스템 리셋 후 상태 정보를 UI로 전송했습니다.")
                    except Exception as e:
                        logger.error(f"리셋 후 상태 정보 전송 실패: {e}")

                    continue

                # 기타 커맨드 처리
                elif cmd_type == "UPDATE_ZONES":
                    zones = command.get("data", [])
                    detector.danger_zone_mapper.update_zones_from_data(zones)
                    logger.info(f"Vision Worker의 Zone 정보가 {len(zones)}개로 업데이트되었습니다.")

            # 2. 영상 프레임 획득
            capture_start_time = time.perf_counter()
            raw_frame = input_adapter.get_frame()
            capture_end_time = time.perf_counter()

            if raw_frame is None:
                await asyncio.sleep(0.1)
                continue
            
            display_frame = raw_frame.copy()
            loop = asyncio.get_running_loop()

            # --- 시스템 잠금 상태 확인 및 처리 ---
            is_locked_now = state_manager.is_locked_status()

            # 1. 잠금 상태로 "전환"되는 순간을 감지하여 전원을 차단합니다.
            if is_locked_now and not was_locked:
                logger.warning("시스템 잠금 상태로 전환됨! 전원을 즉시 차단합니다.")
                control_facade.execute_actions([{"type": "POWER_OFF", "details": {"reason": "System LOCKED"}}])

            # 2. 현재 프레임이 잠금 상태인지 확인하고 UI 처리 및 로직 실행을 결정합니다.
            if is_locked_now:
                # 잠금 상태일 경우, 모든 로직을 중단하고 화면에 경고만 표시
                display_frame = put_text_korean(display_frame, "SYSTEM LOCKED", (15, 50), 30, (0, 0, 255))
                display_frame = put_text_korean(display_frame, "관리자 리셋 필요", (15, 90), 22, (0, 255, 255))
            
            # 3. 시스템 활성화 상태였을 때만 안전 로직 및 시각화 수행
            elif state_manager.is_active():
                sensor_data = input_adapter.get_sensor_data()
                
                # 객체 탐지 (CPU 집약적 작업을 별도 스레드에서 실행하여 이벤트 루프 블로킹 방지)
                detect_start_time = time.perf_counter()
                detection_result = await loop.run_in_executor(None, detector.detect, raw_frame)
                detect_end_time = time.perf_counter()

                # 논리적 상태는 메인 루프에서 직접 가져옴
                current_status = state_manager.get_status()
                current_mode = current_status.get("operation_mode")

                # 물리적 상태는 ControlFacade를 통해 동기적으로 가져옴 (캐시된 상태)
                physical_status = control_facade.get_all_statuses()
                conveyor_is_on = physical_status.get("conveyor_is_on", False)
                conveyor_speed = physical_status.get("conveyor_speed", 100)

                # 로직 처리
                logic_facade_start_time = time.perf_counter()
                logic_result = logic_facade.process(
                    detection_result=detection_result,
                    sensor_data=sensor_data,
                    current_mode=current_mode,
                    current_conveyor_status=conveyor_is_on,
                    current_conveyor_speed=conveyor_speed
                )
                actions = logic_result.get("actions", [])
                current_risk_level = logic_result.get("status", {}).get("risk_level", "SAFE") # LogicFacade가 결정한 위험 등급
                logic_facade_end_time = time.perf_counter()

                # 액션 실행
                control_start_time = time.perf_counter()
                control_actions = []
                for action in actions:
                    action_type = action.get("type")
                    if action_type == 'LOCK_SYSTEM':
                        reason = action.get("details", {}).get("reason", "Logic-driven lock")
                        state_manager.lock_system(reason)
                        # LOCK_SYSTEM은 다른 제어 액션과 함께 처리될 수 있으므로 continue하지 않음

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
                            "log_risk_level": log_risk_level,
                            "operation_mode": current_mode  # 현재 동작 모드 추가
                        }
                        log_queue.put({"type": "LOG", "data": event_data})
                    
                    elif action_type == 'NOTIFY_UI':
                        log_queue.put({"type": "ALERT", "data": action.get("details", {})})

                if control_actions:
                    control_facade.execute_actions(control_actions)
                control_end_time = time.perf_counter()

                # 시각화 및 스트리밍 프레임 업데이트
                draw_start_time = time.perf_counter()
                display_frame = detector.draw_detections(raw_frame, detection_result)
                draw_end_time = time.perf_counter()
                
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

                risk_text = f"Risk: {current_risk_level}"
                risk_color = (0, 0, 255) if current_risk_level in ["CRITICAL", "LOTO_RISK_DETECTED"] else ((0, 165, 255) if current_risk_level == "WARNING" else (0, 255, 0))

                display_frame = put_text_korean(display_frame, mode_text, (15, 50), 22, (255, 255, 0))
                display_frame = put_text_korean(display_frame, status_text, (15, 80), 22, (0, 255, 255))
                display_frame = put_text_korean(display_frame, risk_text, (15, 110), 22, risk_color)

                # --- 실시간 상태 업데이트 메시지 생성 및 전송 ---
                status_message_data = None
                try:
                    # conveyor_status를 변수에서 직접 결정하여 안정성 확보
                    conveyor_final_status = "STOPPED"
                    if final_status.get('conveyor_is_on', False):
                        if final_status.get('conveyor_speed', 100) < 100:
                            conveyor_final_status = "SLOWDOWN"
                        else:
                            conveyor_final_status = "RUNNING"

                    status_message = StatusUpdateMessage(
                        operation_mode=final_status.get('operation_mode', 'N/A'),
                        conveyor_status=conveyor_final_status,
                        conveyor_speed=final_status.get('conveyor_speed', 0),
                        risk_level=current_risk_level,
                        is_locked=final_status.get('is_locked', False) # is_locked 상태 추가
                    )
                    status_message_data = status_message.model_dump()
                except Exception as e:
                    logger.warning(f"상태 업데이트 메시지 생성 실패: {e}")

                if status_message_data and status_message_data != last_status_message_data:
                    log_queue.put({"type": "STATUS_UPDATE", "data": status_message_data})
                    last_status_message_data = status_message_data
            
            else: # state_manager.is_active()가 False일 때
                # 시스템이 비활성화되었을 때, 컨베이어 전원이 켜져 있다면 끈다.
                physical_status = control_facade.get_all_statuses()
                if physical_status.get("conveyor_is_on", False):
                    logger.info("시스템 비활성 상태 확인: 컨베이어 전원을 차단합니다.")
                    control_facade.execute_actions([{"type": "POWER_OFF", "details": {"reason": "System inactive"}}])
                
                display_frame = put_text_korean(display_frame, "SYSTEM INACTIVE", (15, 50), 30, (0, 0, 255))
                await asyncio.sleep(0.1)

            # 4. 처리된 프레임을 FastAPI 서버로 전송
            queue_put_start_time = time.perf_counter()
            if not frame_queue.full():
                # 프레임을 JPEG로 인코딩하여 바이트로 변환
                _, encoded_frame = cv2.imencode('.jpg', display_frame)
                frame_queue.put_nowait(encoded_frame.tobytes())
            queue_put_end_time = time.perf_counter()

            loop_end_time = time.perf_counter()
            
            # --- 성능 측정 로그 ---
            # if state_manager.is_active():
            #     logger.debug(f"[PERF] Capture: {((capture_end_time - capture_start_time) * 1000):.2f}ms | "
            #                  f"Detect: {((detect_end_time - detect_start_time) * 1000):.2f}ms | "
            #                  f"Logic: {((logic_facade_end_time - logic_facade_start_time) * 1000):.2f}ms | "
            #                  f"Control: {((control_end_time - control_start_time) * 1000):.2f}ms | "
            #                  f"Draw: {((draw_end_time - draw_start_time) * 1000):.2f}ms | "
            #                  f"QueuePut: {((queue_put_end_time - queue_put_start_time) * 1000):.2f}ms | "
            #                  f"TOTAL: {((loop_end_time - loop_start_time) * 1000):.2f}ms")

            # --- 다음 루프를 위해 현재 잠금 상태를 저장 ---
            was_locked = is_locked_now

            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"비전 워커 루프에서 예외 발생: {e}", exc_info=True)
            log_queue.put({"type": "LOG", "data": {"event_type": "LOG_SYSTEM_ERROR", "details": {"message": str(e)}, "log_level": "ERROR"}})
            await asyncio.sleep(5)

    # 어플리케이션 종료 시 시리얼 리소스 정리
    communicator.close()
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
    frame_q = Queue(maxsize=20)

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
