import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from firebase_admin import firestore
from google.cloud.firestore import Client
from loguru import logger
from pydantic import ValidationError

from server.db_connector import get_db_client
from server.models.websockets import LogMessage
from .websocket_service import WebSocketService


class DBService:
    """Firestore와 상호작용하여 이벤트 로그를 관리합니다."""

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None, websocket_service: Optional[WebSocketService] = None):
        """
        DBService 초기화. DB 클라이언트를 지연 초기화합니다.
        """
        self._db: Optional[Client] = None
        self.loop = loop
        self.websocket_service = websocket_service
        self.collection_name = "event_logs"
        logger.success("DBService 초기화 완료 (DB 클라이언트는 첫 사용 시 연결됩니다).")

    @property
    def db(self) -> Client:
        """DB 클라이언트에 처음 접근할 때 지연 초기화를 수행합니다."""
        if self._db is None:
            self._db = get_db_client()
        return self._db

    def get_status(self) -> dict:
        """Firestore 클라이언트의 상태를 확인합니다."""
        return {
            "status": "connected" if self.db else "disconnected",
            "details": f"Connected to collection '{self.collection_name}'" if self.db else "Firestore client not provided.",
        }

    async def log_event(self, event_data: Dict[str, Any]):
        """
        Firestore에 이벤트를 비동기적으로 기록하고, WebSocket 방송을 요청합니다.
        """
        try:
            # 1. 데이터 준비 및 검증
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.now().isoformat()

            # LogMessage 모델을 사용하여 데이터 검증
            try:
                log_message = LogMessage(**event_data)
                validated_data = log_message.model_dump()
                logger.success(f"로그 데이터 검증 성공: {log_message.event_type}")
            except ValidationError as e:
                logger.error(f"웹소켓 로그 데이터 검증 실패: {e}")
                # 검증에 실패하더라도 로그는 남기되, 원본 데이터를 사용
                validated_data = event_data

            # 2. DB에 데이터 비동기적으로 저장
            def db_write_sync():
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

            db_success = await self.loop.run_in_executor(None, db_write_sync)

            # 3. WebSocketService에 'logs' 채널로 방송 위임
            if db_success and self.websocket_service:
                await self.websocket_service.broadcast_to_channel('logs', validated_data)
            
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
