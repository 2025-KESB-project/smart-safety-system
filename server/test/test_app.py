# server/test_app.py
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 프론트엔드(localhost:3000)에서의 접속을 허용하기 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    """
    웹소켓 연결을 테스트하기 위한 최소 기능 엔드포인트.
    연결을 수락하고, 1초마다 카운트를 클라이언트로 전송합니다.
    """
    await websocket.accept()
    print("✅ 클라이언트와 웹소켓 연결 성공!")
    
    count = 0
    try:
        while True:
            # 1초마다 클라이언트로 현재 카운트를 JSON 형식으로 보냅니다.
            await websocket.send_json({"id": f"test_{count}", "message": f"서버 카운트: {count}"})
            print(f"Sent: {count}")
            count += 1
            await asyncio.sleep(1) # 비동기 sleep을 위해 asyncio.sleep 사용
            
    except WebSocketDisconnect:
        print("❌ 클라이언트와 연결이 끊어졌습니다.")
    except Exception as e:
        print(f"💥 에러 발생: {e}")

# 이 파일을 직접 실행했을 때 uvicorn 서버가 실행되도록 설정
if __name__ == "__main__":
    print("테스트 웹소켓 서버를 http://localhost:8000 에서 시작합니다.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
