import asyncio
from typing import Dict, Any
from loguru import logger
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client
from pydantic import ValidationError

from .websocket_service import WebSocketService
from server.models.websockets import LogMessage # LogMessage 모델 임포트

class DBService:
    """
    Firestore 데이터베이스 작업을 관리하고,
    새로운 로그 발생 시 Pydantic 모델로 검증 후 WebSocketService에 방송을 위임합니다.
    (비동기 방식으로 리팩토링됨)
    """

    def __init__(self, db: Client, loop: asyncio.AbstractEventLoop, websocket_service: WebSocketService):
        """
        DBService를 초기화합니다.
        """
        if not isinstance(db, Client):
            raise TypeError("db must be an instance of google.cloud.firestore_v1.client.Client")
        
        self.db = db
        self.loop = loop
        self.websocket_service = websocket_service
        self.collection_name = 'event_logs'
        
        logger.success("DBService 초기화 완료 (WebSocket 방송 위임).")

    def get_status(self) -> dict:
        """Firestore 클라이언트의 상태를 확인합니다."""
        return {
            "status": "connected" if self.db else "disconnected",
            "details": f"Connected to collection '{self.collection_name}'" if self.db else "Firestore client not provided.",
        }

    async def log_event(self, event_data: Dict[str, Any]):
        """
        Firestore에 이벤트를 비동기적으로 기록하고, Pydantic 모델로 검증 후
        WebSocketService에 방송을 요청합니다.
        """
        try:
            # 1. 웹소켓으로 보낼 데이터 준비 및 검증
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.now().isoformat()

            log_message = LogMessage(**event_data)
            validated_data = log_message.model_dump()
            logger.success(f"로그 데이터 검증 성공: {log_message.event_type}")

            # 2. DB에 데이터 저장 (동기 I/O 작업을 이벤트 루프를 막지 않도록 처리)
            def db_write():
                try:
                    event_data_for_db = validated_data.copy()
                    event_data_for_db['timestamp'] = firestore.SERVER_TIMESTAMP
                    collection_ref = self.db.collection(self.collection_name)
                    collection_ref.add(event_data_for_db)
                    logger.info(f"이벤트 로그 DB 저장 성공: {validated_data.get('event_type')}")
                    return True
                except Exception as e:
                    logger.error(f"DB 쓰기 작업 중 오류 발생: {e}")
                    return False

            db_success = await self.loop.run_in_executor(None, db_write)

            # 3. DB 저장이 성공했을 때만 WebSocketService에 방송 위임
            if db_success:
                await self.websocket_service.broadcast_to_channel('logs', validated_data)
            
        except ValidationError as e:
            logger.error(f"웹소켓 로그 데이터 검증 실패: {e}")
        except Exception as e:
            logger.error(f"이벤트 로그 저장 또는 방송 중 오류 발생: {e}")

    def get_events(self, limit: int = 50) -> list:
        """Firestore에서 최근 이벤트 목록을 가져옵니다."""
        try:
            collection_ref = self.db.collection(self.collection_name)
            query = collection_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event = doc.to_dict()
                if 'timestamp' in event and hasattr(event['timestamp'], 'isoformat'):
                    event['timestamp'] = event['timestamp'].isoformat()
                events.append(event)
            return events
        except Exception as e:
            logger.error(f"이벤트 로그 조회 중 오류 발생: {e}")
            return []
