import cv2
import time
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any

# 상위 디렉터리의 모듈을 가져오기 위한 경로 설정
import sys
sys.path.append(str(Path(__file__).parent.parent))
from input_adapter.input_facade import InputAdapter
from detect.detect_facade import Detector

# --- 설정 ---
INPUT_CONFIG = {
    'camera_index': 0,
    'mock_mode': False
}
DETECTOR_CONFIG = {
    'person_detector': {'model_path': 'yolov8n.pt'},
    'pose_detector': {
        'pose_model_path': 'yolov8n-pose.pt',
        'fall_model_path': 'fall_det_1.pt'
    }
    # danger_zone_mapper 설정은 더 이상 여기서 필요하지 않음
}
ZONE_CONFIG_PATH = 'detect/danger_zones.json' # 로컬 JSON 파일 경로
WINDOW_NAME = "Input -> Detect Layer Test"

class MockZoneService:
    """
    테스트를 위한 가짜 ZoneService.
    Firestore 대신 로컬 JSON 파일에서 위험 구역 정보를 로드합니다.
    """
    def __init__(self, config_path: str):
        self._zones = []
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._zones = json.load(f)
            logger.info(f"MockZoneService: '{config_path}'에서 {len(self._zones)}개의 구역 로드 완료.")
        except Exception as e:
            logger.error(f"MockZoneService: '{config_path}' 파일 로드 실패: {e}")

    def get_all_zones(self) -> List[Dict[str, Any]]:
        """로드된 모든 구역 정보를 반환합니다."""
        return self._zones

def main():
    logger.info("Input -> Detect 파이프라인 테스트를 시작합니다...")

    # 1. InputAdapter 및 Detector 초기화
    try:
        # 테스트용 MockZoneService를 생성하여 Detector에 주입
        mock_zone_service = MockZoneService(config_path=ZONE_CONFIG_PATH)
        
        input_adapter = InputAdapter(**INPUT_CONFIG)
        detector = Detector(config=DETECTOR_CONFIG, zone_service=mock_zone_service)
        
        logger.success("InputAdapter와 Detector 초기화 완료.")
    except Exception as e:
        logger.error(f"모듈 초기화 실패: {e}", exc_info=True)
        return

    cv2.namedWindow(WINDOW_NAME)
    logger.info(f"스트림 시작. [{WINDOW_NAME}] 창에서 'q' 키를 누르면 종료됩니다.")

    prev_time = 0
    while True:
        # 2. InputAdapter를 통해 입력 데이터 가져오기
        input_data = input_adapter.get_input()
        if input_data is None or input_data.get('frame') is None:
            logger.warning("입력 스트림이 종료되었거나 프레임을 가져올 수 없습니다.")
            break

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