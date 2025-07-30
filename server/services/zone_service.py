from google.cloud.firestore_v1.client import Client
from loguru import logger
from typing import List, Dict, Any, Optional

class ZoneService:
    """
    Firestore 'danger_zones' 컬렉션과 상호작용하여
    위험 구역 데이터를 관리하는 서비스 클래스.
    """
    def __init__(self, db: Client, collection_name: str = 'danger_zones'):
        """
        ZoneService를 초기화합니다.

        Args:
            db (Client): 이미 초기화된 Firestore 클라이언트 객체.
            collection_name (str): 사용할 Firestore 컬렉션 이름.
        """
        if not isinstance(db, Client):
            raise TypeError("db must be an instance of google.cloud.firestore_v1.client.Client")
        self.db = db
        self.collection_ref = self.db.collection(collection_name)
        logger.success(f"ZoneService initialized for collection '{collection_name}'.")

    def get_all_zones(self) -> List[Dict[str, Any]]:
        """컬렉션의 모든 위험 구역 문서를 가져옵니다."""
        try:
            docs = self.collection_ref.stream()
            zones = []
            for doc in docs:
                zone_data = doc.to_dict()
                zone_data['id'] = doc.id
                zones.append(zone_data)
            logger.info(f"{len(zones)}개의 위험 구역 정보를 DB에서 조회했습니다.")
            return zones
        except Exception as e:
            logger.error(f"모든 위험 구역 정보 조회 중 오류 발생: {e}")
            return []

    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """특정 ID의 위험 구역 문서를 가져옵니다."""
        try:
            doc_ref = self.collection_ref.document(zone_id)
            doc = doc_ref.get()
            if doc.exists:
                zone_data = doc.to_dict()
                zone_data['id'] = doc.id
                return zone_data
            return None
        except Exception as e:
            logger.error(f"'{zone_id}' 구역 정보 조회 중 오류 발생: {e}")
            return None

    def add_or_update_zone(self, zone_id: str, zone_data: Dict[str, Any]) -> bool:
        """새로운 위험 구역을 추가하거나 기존 구역을 업데이트합니다."""
        try:
            zone_data_to_save = zone_data.copy()
            if 'id' in zone_data_to_save:
                del zone_data_to_save['id']
            self.collection_ref.document(zone_id).set(zone_data_to_save)
            logger.success(f"'{zone_id}' 구역 정보를 DB에 성공적으로 저장/업데이트했습니다.")
            return True
        except Exception as e:
            logger.error(f"'{zone_id}' 구역 정보 저장/업데이트 중 오류 발생: {e}")
            return False

    def delete_zone(self, zone_id: str) -> bool:
        """특정 ID의 위험 구역 문서를 삭제합니다."""
        try:
            self.collection_ref.document(zone_id).delete()
            return True
        except Exception as e:
            logger.error(f"'{zone_id}' 구역 정보 삭제 중 오류 발생: {e}")
            return False

    def register_listener(self, callback) -> None:
        """
        'danger_zones' 컬렉션에 대한 실시간 리스너(on_snapshot)를 등록합니다.
        컬렉션에 변경이 있을 때마다 제공된 콜백 함수가 호출됩니다.

        Args:
            callback: 변경 사항을 처리할 콜백 함수.
                      이 함수는 (doc_snapshot, changes, read_time)을 인자로 받습니다.
        """
        try:
            self.collection_ref.on_snapshot(callback)
            logger.info(f"'{self.collection_ref.id}' 컬렉션에 대한 실시간 리스너를 성공적으로 등록했습니다.")
        except Exception as e:
            logger.error(f"실시간 리스너 등록 중 심각한 오류 발생: {e}")