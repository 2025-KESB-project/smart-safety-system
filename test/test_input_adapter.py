from input_adapter.adapter import InputAdapter
import cv2

def main():
    adapter = InputAdapter(camera_index=0, sensor_pin=17)

    while True:
        inputs = adapter.get_input()
        frame = inputs['raw_frame']
        sensor_data = inputs['sensor_data']

        # 센서 데이터 출력
        print(f"Sensor value: {sensor_data}")

        # 카메라 프레임 출력
        cv2.imshow("Raw Frame", frame)
        cv2.imshow("Preprocessed Frame", inputs['frame'])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    adapter.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()