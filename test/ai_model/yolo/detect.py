# ai_model/yolo/detect.py
import torch
import cv2
from pathlib import Path
import os

# 모델 로드
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # or yolov5m/l/x

#webcam (기본 카메라 : 0)
cap = cv2.VideoCapture(3)

while cap.isOpened():
    # 프레임 읽기
    # ret는 프레임이 제대로 읽혔는지 여부 (boolean)
    ret, frame = cap.read()
    if not ret:
        print("카메라 프레임을 읽을 수 없습니다.")
        break

    results = model(frame)

    # 결과에서 bbox 좌표 가져오기
    detections = results.xyxy[0]

    # 감지된 객체 박스 그리기
    for *box, conf, cls in detections:
        x1, y1, x2, y2 = map(int, box)
        label = model.names[int(cls)]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 프레임 출력
    cv2.imshow('YOLO Real-time Detection', frame)

    #q 키 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


# def detect_person(image_path, save_dir='result_images'):
#     results = model(image_path)
#
#     #결과 저장
#     results.save(save_dir=save_dir)
#
#     # 결과를 pandas DataFrame 형태로 반환
#     return results.pandas().xyxy[0]

# if __name__ == '__main__':
#     test_image = 'test_images/test1.jpg'
#     detections = detect_person(test_image)
#     print(detections)