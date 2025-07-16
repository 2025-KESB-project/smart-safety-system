import cv2
import mediapipe as mp

mp_hand = mp.solutions.hands
hands = mp_hand.Hands(static_image_mode=False,max_num_hands=1,min_detection_confidence=0.7)
mp_drawing= mp.solutions.drawing_utils

def is_v_sign(hand_landmarks):
    lm = hand_landmarks.landmark
    # 손가락 펴짐/접힘 상태 (y 값이 작을수록 위로 펴짐)
    index_extended = lm[8].y < lm[6].y
    middle_extended = lm[12].y < lm[10].y
    ring_folded = lm[16].y > lm[14].y
    pinky_folded = lm[20].y > lm[18].y

    return index_extended and middle_extended and ring_folded and pinky_folded

cap =cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame =cv2.flip(frame,1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hand.HAND_CONNECTIONS)

            if is_v_sign(hand_landmarks):
                cv2.putText(frame,'Warning: V Sign Detected!',(10, 70),cv2.FONT_HERSHEY_SIMPLEX,1,(0, 0, 255),2)

    cv2.imshow("Finger Counter", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
      
cap.release()
cv2.destroyAllWindows()