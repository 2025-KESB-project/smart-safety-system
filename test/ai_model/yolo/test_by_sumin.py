from ultralytics import YOLO
import cv2
import numpy as np
pose_model = YOLO('yolov8n-pose.pt')  # replace with your pose model path

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

    for det in model([frame], stream=True):
        annotated_frame = det.plot()  # detection overlay
        # two-stage: pose estimation for each detected person
        for box in det.boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = map(int, box)
            # crop person region
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            # run pose model
            pose_res = pose_model(crop, imgsz=640)[0]
            # draw keypoints
            for kp in pose_res.keypoints.cpu().numpy()[0]:
                # kp format: [x, y, confidence]
                px, py, conf = kp
                # map back to full frame
                ix, iy = int(px) + x1, int(py) + y1
                cv2.circle(annotated_frame, (ix, iy), 3, (0,255,255), -1)
        cv2.imshow("YOLOv8 Real-time with Pose", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 종료
cap.release()
cv2.destroyAllWindows()