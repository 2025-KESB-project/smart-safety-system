import time
import cv2
import numpy as np
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from multiprocessing import Queue

from server.dependencies import get_frame_queue

router = APIRouter()

def create_placeholder_image(text: str):
    """지정된 텍스트로 간단한 플레이스홀더 이미지를 생성합니다."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    lines = text.split('\n')
    y0, dy = 220, 30
    for i, line in enumerate(lines):
        y = y0 + i * dy
        cv2.putText(img, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return img

def generate_frames(frame_queue: Queue):
    """
    Vision Worker로부터 frame_queue를 통해 받은 프레임을 반환하는 제너레이터.
    """
    last_frame_time = time.time()
    
    while True:
        if not frame_queue.empty():
            encoded_frame_bytes = frame_queue.get_nowait()
            last_frame_time = time.time()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                   encoded_frame_bytes + b'\r\n')
        else:
            # 5초 이상 새 프레임이 없으면 경고 이미지 전송
            if time.time() - last_frame_time > 5.0:
                placeholder = create_placeholder_image("Vision Worker not responding...\nCheck server logs.")
                _, encoded_image = cv2.imencode(".jpg", placeholder)
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                       encoded_image.tobytes() + b'\r\n')
                time.sleep(1)
            else:
                time.sleep(0.01) # 짧은 대기

@router.get("/video_feed", summary="실시간 영상 스트리밍")
def video_feed(frame_queue: Queue = Depends(get_frame_queue)):
    """
    Vision Worker로부터 받은 영상 스트림을 MJPEG 형식으로 제공합니다.
    """
    return StreamingResponse(generate_frames(frame_queue), media_type="multipart/x-mixed-replace; boundary=frame")