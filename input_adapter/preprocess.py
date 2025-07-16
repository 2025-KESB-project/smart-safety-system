import cv2

class VideoPreprocessor:
    def __init__(self):
        pass

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (416, 416))
        return resized