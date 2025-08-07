from typing import List, Dict, Any, Optional, Callable
from loguru import logger
from google.cloud.firestore import Client, DocumentSnapshot, Query
from google.api_core.exceptions import GoogleAPICallError

# from core.models import Zone, ZoneUpdate

class ZoneService:
    """위험 구역(Danger Zone)의 CRUD 및 관리를 담당합니다."""

    def __init__(self, use_firestore: bool = True):
        """
        ZoneService 초기화.
        use_firestore 플래그에 따라 Firestore DB 또는 인메모리 저장을 사용합니다.
        """
        self.use_firestore = use_firestore
        self._db: Optional[Client] = None
        self.collection_name = "danger_zones"
        self.zones_in_memory: List[Dict[str, Any]] = []
        
        if self.use_firestore:
            from server.db_connector import get_db_client # 지연 임포트
            self.get_db_client = get_db_client
            logger.success(f"ZoneService initialized for Firestore collection '{self.collection_name}'.")
        else:
            logger.warning("ZoneService initialized in in-memory mode. DB will not be used.")

    def load_zones_from_data(self, zones_data: List[Dict[str, Any]]):
        """인메모리 모드에서 외부 데이터로 위험 구역을 전체 업데이트합니다."""
        if self.use_firestore:
            logger.warning("load_zones_from_data is only available in in-memory mode.")
            return
        self.zones_in_memory = zones_data
        logger.info(f"In-memory zones updated with {len(zones_data)} zones.")

    @property
    def db(self) -> Client:
        """DB 클라이언트에 처음 접근할 때 지연 초기화를 수행합니다."""
        if self._db is None:
            if not self.use_firestore:
                raise RuntimeError("Firestore is not enabled for this ZoneService instance.")
            self._db = self.get_db_client()
        return self._db

    @property
    def collection_ref(self):
        """컬렉션 참조에 처음 접근할 때 초기화를 수행합니다."""
        return self.db.collection(self.collection_name)

    def get_all_zones(self) -> List[Dict[str, Any]]:
        """컬렉션의 모든 위험 구역 문서를 가져옵니다."""
        if not self.use_firestore:
            return self.zones_in_memory

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
        if not self.use_firestore:
            return next((zone for zone in self.zones_in_memory if zone.get('id') == zone_id), None)

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
        if not self.use_firestore:
            existing_zone = self.get_zone(zone_id)
            if existing_zone:
                existing_zone.update(zone_data)
            else:
                new_zone = {"id": zone_id, **zone_data}
                self.zones_in_memory.append(new_zone)
            return True

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
        if not self.use_firestore:
            initial_len = len(self.zones_in_memory)
            self.zones_in_memory = [zone for zone in self.zones_in_memory if zone.get('id') != zone_id]
            return len(self.zones_in_memory) < initial_len

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