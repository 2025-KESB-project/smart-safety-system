import cv2
import time
from pathlib import Path
from loguru import logger

# 상위 디렉터리의 모듈을 가져오기 위한 경로 설정
import sys
sys.path.append(str(Path(__file__).parent.parent))
from detect.detector import Detector
from detect.danger_zone_creator import ZoneCreator

# --- 설정 ---
CAMERA_INDEX = 3
CONFIG_FILE = "danger_zones.json"
WINDOW_NAME = "test"

DETECTOR_CONFIG = {
    'person_detector': {'model_path': 'yolov8n.pt'},
    'pose_detector': {'model_path': 'yolov8n-pose.pt'},
    'danger_zone_mapper': {'zone_config_path': CONFIG_FILE}
}

def main():
    logger.info("통합 테스트 및 설정 모드를 시작합니다...")

    # 1. 모듈 초기화
    try:
        detector = Detector(DETECTOR_CONFIG)
        cv2.namedWindow(WINDOW_NAME)
        zone_creator = ZoneCreator(window_name=WINDOW_NAME, config_path=CONFIG_FILE, 
                                  danger_zone_mapper=detector.danger_zone_mapper)
        logger.success("모든 모듈 초기화 완료.")
    except Exception as e:
        logger.error(f"모듈 초기화 실패: {e}")
        return

    # 2. 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        logger.error(f"카메라(인덱스: {CAMERA_INDEX})를 열 수 없습니다.")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    logger.info(f"스트림 시작. [{WINDOW_NAME}] 창을 클릭하여 활성화한 후 키를 입력하세요:")
    logger.info("  - 'd': 그리기 모드 시작/종료 (Toggle)")
    logger.info("  - 's': (그리기 모드에서) 구역 저장")
    logger.info("  - 'c': (그리기 모드에서) 구역 그리기 취소")
    logger.info("  - 'q': 프로그램 종료")

    prev_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        # 'd' 키를 최상위에서 토글로 처리
        if key == ord('d'):
            if zone_creator.is_drawing:
                zone_creator.cancel_drawing() # 그리기 모드 중 d를 누르면 취소
            else:
                zone_creator.start_drawing() # 탐지 모드 중 d를 누르면 시작

        if zone_creator.is_drawing:
            # --- 구역 설정 모드 ---
            if key == ord('s'):
                if len(zone_creator.points) >= 3:
                    cv2.putText(display_frame, "PAUSED: Check Terminal to input Zone ID and Name", 
                                (50, display_frame.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    cv2.imshow(WINDOW_NAME, display_frame)
                    cv2.waitKey(1)

                    zone_id = input("\n[INPUT] 새로운 구역의 ID를 입력하세요 (취소: Enter): ")
                    if zone_id:
                        zone_name = input(f"[INPUT] 구역 '{zone_id}'의 이름을 입력하세요: ")
                        if zone_name:
                            zone_creator.save_current_zone(zone_id, zone_name)
                        else:
                            logger.warning("이름이 입력되지 않아 저장 취소.")
                            zone_creator.cancel_drawing()
                    else:
                        logger.warning("ID가 입력되지 않아 저장 취소.")
                        zone_creator.cancel_drawing()
                else:
                    logger.warning("저장하려면 최소 3개의 점이 필요합니다.")
            
            elif key == ord('c'):
                zone_creator.cancel_drawing()
            
            display_frame = zone_creator.draw_creation_feedback(display_frame)
        
        else: # not zone_creator.is_drawing
            # --- 실시간 탐지 모드 ---
            detection_result = detector.detect(display_frame)
            display_frame = detector.draw_detections(display_frame, detection_result)

            current_time = time.time()
            if prev_time > 0:
                fps = 1 / (current_time - prev_time)
                cv2.putText(display_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            prev_time = current_time

        cv2.imshow(WINDOW_NAME, display_frame)

    cap.release()
    cv2.destroyAllWindows()
    logger.info("프로그램을 종료합니다.")

if __name__ == '__main__':
    main()
