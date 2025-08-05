

import cv2
import numpy as np
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger
import time

router = APIRouter()

def create_placeholder_image(text: str):
    """지정된 텍스트로 간단한 플레이스홀더 이미지를 생성합니다."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # 텍스트를 여러 줄로 나눕니다.
    lines = text.split('\n')
    y0, dy = 220, 30
    for i, line in enumerate(lines):
        y = y0 + i * dy
        cv2.putText(img, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return img

def generate_frames(latest_frame_provider):
    """
    처리된 최신 프레임을 지속적으로 반환하는 제너레이터 함수.
    프레임을 사용할 수 없는 경우, 대체 이미지를 전송합니다.
    """
    last_frame_time = time.time()
    
    while True:
        frame = latest_frame_provider()
        
        if frame is None:
            # 5초 이상 프레임이 없으면 경고 메시지 표시
            if time.time() - last_frame_time > 5.0:
                placeholder = create_placeholder_image("Camera feed not available.\nCheck background worker logs.")
                (flag, encodedImage) = cv2.imencode(".jpg", placeholder)
                if flag:
                    yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                           bytearray(encodedImage) + b'\r\n')
                    time.sleep(1) # 1초마다 대체 이미지 전송
                continue
            
            # 초기화 중이거나 일시적인 문제일 수 있으므로 잠시 대기
            time.sleep(0.1)
            continue

        # 프레임이 있으면 마지막 시간을 업데이트
        last_frame_time = time.time()
        
        # 프레임을 JPEG 형식으로 인코딩
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue

        # 클라이언트로 전송할 데이터 형식으로 변환하여 yield
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
               bytearray(encodedImage) + b'\r\n')
        time.sleep(0.01) # 다른 작업에 CPU를 양보하기 위한 짧은 대기

@router.get("/video_feed", summary="실시간 영상 스트리밍")
def video_feed(request: Request):
    """
    실시간으로 처리되는 영상 스트림을 MJPEG 형식으로 제공합니다.
    HTML의 <img> 태그 src 속성에 이 엔드포인트를 직접 사용할 수 있습니다.
    """
    def get_frame():
        return getattr(request.app.state, 'latest_frame', None)
    
    return StreamingResponse(generate_frames(get_frame), media_type="multipart/x-mixed-replace; boundary=frame")



