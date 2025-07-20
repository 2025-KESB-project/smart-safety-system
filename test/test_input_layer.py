import cv2
from input_adapter.adapter import InputAdapter

def main():
    adapter = InputAdapter(camera_index=3)
    print("[INFO] ESC 키를 누르면 종료됩니다.")
    while True:
        data = adapter.get_input()
        if data is None:
            print("[WARN] 프레임을 가져오지 못했습니다.")
            break
        frame = data["frame"]
        sensor_str = str(data["sensor_data"])
        # 센서값을 프레임 좌상단에 표시
        cv2.putText(frame, sensor_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        cv2.imshow("InputAdapter Test (ESC to quit)", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    adapter.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()  