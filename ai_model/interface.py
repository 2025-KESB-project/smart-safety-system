# ai_model/inference.py
from yolo.detect import detect_objects
from openpose.pose_detect import detect_pose

def run_inference(image_path):
    yolo_results = detect_objects(image_path)
    pose_results = detect_pose(image_path)

    print("YOLO 감지 결과:", yolo_results.pandas().xyxy[0])
    print("OpenPose 자세 인식 결과:", pose_results)

    # 이후 판단 계층에 결과 전달 예정