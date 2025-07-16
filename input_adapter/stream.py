import cv2



class VideoStream:
    """다양한 비디오 소스를 처리하는 스트림 클래스"""

    """다양한 비디오 소스를 처리하는 스트림 클래스"""
    def __init__(self, source=0, resolution=(640, 480), fps=30):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, fps)

    def get_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame

    def release(self):
        """비디오 캡처 객체를 해제합니다."""
        self.cap.release()
