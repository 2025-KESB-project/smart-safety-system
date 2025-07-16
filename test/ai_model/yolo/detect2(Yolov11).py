
from ultralytics import YOLO
import cv2

# --------------------------------------------------
# 1) 모델 로드  ─────────────────────────────────────
#    - 'n / s / m / l / x' 5종 스케일 제공
#    - 첫 실행 시 *.pt 가중치 자동 다운로드(또는 로컬 경로 지정)
# --------------------------------------------------
model = YOLO('yolov11n.pt')          # 소형 모델 (권장)

# --------------------------------------------------
# 2) 비디오 캡처  ──────────────────────────────────
#    - 노트북 내장 웹캠 0, 외장 1… / RTSP 주소도 가능
# --------------------------------------------------
cap = cv2.VideoCapture(3)
if not cap.isOpened():
    raise RuntimeError('카메라 열기 실패')

while True:
    ret, frame = cap.read()
    if not ret:
        print('프레임 수신 오류 ― 스트림 종료')
        break

    # ------------------------------------------------
    # 3) YOLO v11 추론
    #    stream=True 옵션 → 제너레이터 형태로 실시간 결과 반환
    # ------------------------------------------------
    results = model.predict(frame, imgsz=640, stream=True)  # stream=True 도 가능

    # 4) 결과 시각화 (Ultralytics 내장 함수)
    annotated = results[0].plot()         # bbox·라벨·conf 자동 렌더링
    cv2.imshow('YOLO v11 Detection', annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()