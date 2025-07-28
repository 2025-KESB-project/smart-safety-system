import cv2
import time
from pathlib import Path
from loguru import logger

# 상위 디렉터리의 모듈을 가져오기 위한 경로 설정
import sys
sys.path.append(str(Path(__file__).parent.parent))
from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector

# --- 설정 ---
# InputAdapter 설정
# mock_mode=False로 설정하여 실제 카메라를 사용합니다.
INPUT_CONFIG = {
    'camera_index': 0,
    'mock_mode': False
}

# Detector 설정
DETECTOR_CONFIG = {
    'person_detector': {'model_path': 'yolov8n.pt'},
    'pose_detector': {
        'pose_model_path': 'yolov8n-pose.pt',
        'fall_model_path': 'fall_det_1.pt'
    },
    'danger_zone_mapper': {'zone_config_path': 'detect/danger_zones.json'}
}

WINDOW_NAME = "Input -> Detect Layer Test"

def main():
    logger.info("Input -> Detect 파이프라인 테스트를 시작합니다...")

    # 1. InputAdapter 및 Detector 초기화
    try:
        input_adapter = InputAdapter(**INPUT_CONFIG)
        detector = Detector(DETECTOR_CONFIG)
        logger.success("InputAdapter와 Detector 초기화 완료.")
    except Exception as e:
        import inspect, detect.pose_detector as pd
        print("POSE FILE:", pd.__file__, "\nPOSE SIG :", inspect.signature(pd.PoseDetector.__init__))
        logger.error(f"모듈 초기화 실패: {e}")
        return

    cv2.namedWindow(WINDOW_NAME)
    logger.info(f"스트림 시작. [{WINDOW_NAME}] 창에서 'q' 키를 누르면 종료됩니다.")

    prev_time = 0
    while True:
        # 2. InputAdapter를 통해 입력 데이터 가져오기
        # get_input()은 전처리된 프레임, 원본 프레임, 센서 데이터를 반환합니다.
        input_data = input_adapter.get_input()
        if input_data is None or input_data.get('frame') is None:
            logger.warning("입력 스트림이 종료되었거나 프레임을 가져올 수 없습니다.")
            break

        # Detector는 전처리되지 않은 원본 프레임을 사용하는 것이 더 정확할 수 있습니다.
        # 여기서는 원본 프레임(raw_frame)을 사용합니다.
        raw_frame = input_data['raw_frame']

        # 3. Detector를 사용하여 탐지 수행
        detection_result = detector.detect(raw_frame)

        # 4. 탐지 결과를 프레임에 시각화
        display_frame = detector.draw_detections(raw_frame, detection_result)

        # 5. FPS 계산 및 표시
        current_time = time.time()
        if prev_time > 0:
            fps = 1 / (current_time - prev_time)
            cv2.putText(display_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        prev_time = current_time

        # 6. 화면에 결과 프레임 출력
        cv2.imshow(WINDOW_NAME, display_frame)

        # 'q' 키를 누르면 루프 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 7. 자원 해제
    input_adapter.release()
    cv2.destroyAllWindows()
    logger.info("테스트를 종료합니다.")

if __name__ == '__main__':
    main()