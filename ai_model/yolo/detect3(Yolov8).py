from ultralytics import YOLO
import cv2

# YOLOv8 모델 로드 (yolov8n.pt, yolov8s.pt 등 사전 학습된 모델 사용 가능)
model = YOLO('yolov8n.pt')  # 또는 'yolov8s.pt', 'yolov8m.pt' 등

# 웹캠 열기
cap = cv2.VideoCapture(3)

if not cap.isOpened():
    print("❌ 카메라 열기 실패")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    # stream=True 옵션을 사용하여 실시간 추론
    # stream=false로 설정하면 한 번에 모든 결과를 반환
    # YOLOv8 추론 (이미지 프레임을 넘기면 자동으로 박스 등 추가됨)
    for result in model([frame], stream=True):
        annotated_frame = result.plot()
        cv2.imshow("YOLO Detection", annotated_frame)
    # results = model(frame, imgsz=640, stream=True)
    #
    # # 시각화된 결과 이미지 얻기
    # annotated_frame = results[0].plot()

    # 화면에 표시
    # cv2.imshow("YOLOv8 Real-time Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 종료
cap.release()
cv2.destroyAllWindows()