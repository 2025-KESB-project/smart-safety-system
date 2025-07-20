import mediapipe as mp
import cv2

class HandGestureDetector:
    def __init__(self):
        self.hands = mp.python.solutions.hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            max_num_hands=2
        )

    def detect_gesture(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        gestures = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 간단 예시: 손이 위로 들렸는지, V 표시 등
                # 실제 구현은 landmark 좌표로 분석 필요
                gestures.append("hand_up")  # 예시
        return gestures