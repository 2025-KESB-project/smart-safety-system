from fastapi import APIRouter, Depends, HTTPException, Body, status
from typing import List
from loguru import logger

from ..services.zone_service import ZoneService
from ..dependencies import get_zone_service
from ..models.zone import DangerZone, DangerZoneCreate, ZoneResponse, Point

router = APIRouter(
    prefix="/api/zones",
    tags=["위험 구역 (Danger Zones)"]
)

@router.get("/", response_model=List[DangerZone], summary="모든 위험 구역 조회")
def get_all_zones(zone_service: ZoneService = Depends(get_zone_service)):
    """설정된 모든 위험 구역의 목록을 조회합니다."""
    try:
        zones_data = zone_service.get_all_zones()
        # Firestore에서 받은 데이터(points가 map의 배열)를 Pydantic 모델(Point 객체의 리스트)로 변환
        # 참고: Firestore는 2차원 배열을 직접 지원하지 않아, [{x: 값, y: 값}, ...] 형태로 저장해야 함
        return [
            DangerZone(
                id=zone.get('id'),
                name=zone.get('name'),
                points=[Point(x=p.get('x', 0), y=p.get('y', 0)) for p in zone.get('points', [])]
            ) for zone in zones_data
        ]
    except Exception as e:
        logger.error(f"API 오류: 모든 위험 구역 조회 실패 - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="서버 내부 오류가 발생했습니다.")

@router.get("/{zone_id}", response_model=DangerZone, summary="특정 위험 구역 조회")
def get_zone_by_id(zone_id: str, zone_service: ZoneService = Depends(get_zone_service)):
    """고유 ID를 사용하여 단일 위험 구역을 조회합니다."""
    zone = zone_service.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID가 '{zone_id}'인 구역을 찾을 수 없습니다.")
    
    return DangerZone(
        id=zone.get('id'),
        name=zone.get('name'),
        points=[Point(x=p.get('x', 0), y=p.get('y', 0)) for p in zone.get('points', [])]
    )

@router.post("/", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED, summary="새로운 위험 구역 생성")
def create_zone(
    zone_id: str = Body(..., embed=True, description="새 구역의 고유 ID"),
    zone_data: DangerZoneCreate = Body(..., embed=True, description="새 구역의 데이터"),
    zone_service: ZoneService = Depends(get_zone_service)
):
    """지정된 ID와 데이터로 새로운 위험 구역을 생성합니다."""
    if zone_service.get_zone(zone_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"ID가 '{zone_id}'인 구역이 이미 존재합니다.")
    
    # Pydantic 모델을 DB에 저장할 딕셔너리로 변환
    zone_dict = zone_data.model_dump()
    
    zone_service.add_or_update_zone(zone_id, zone_dict)
    return ZoneResponse(status="success", message=f"'{zone_id}' 구역이 성공적으로 생성되었습니다.", zone_id=zone_id)

@router.put("/{zone_id}", response_model=ZoneResponse, summary="위험 구역 정보 업데이트")
def update_zone(
    zone_id: str,
    zone_data: DangerZoneCreate,
    zone_service: ZoneService = Depends(get_zone_service)
):
    """기존 위험 구역의 이름과 좌표를 업데이트합니다."""
    if not zone_service.get_zone(zone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID가 '{zone_id}'인 구역을 찾을 수 없습니다.")
    
    zone_dict = zone_data.model_dump()
    zone_service.add_or_update_zone(zone_id, zone_dict)
    return ZoneResponse(status="success", message=f"'{zone_id}' 구역이 성공적으로 업데이트되었습니다.", zone_id=zone_id)

@router.delete("/{zone_id}", response_model=ZoneResponse, summary="위험 구역 삭제")
def delete_zone(zone_id: str, zone_service: ZoneService = Depends(get_zone_service)):
    """고유 ID를 사용하여 위험 구역을 삭제합니다."""
    if not zone_service.get_zone(zone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID가 '{zone_id}'인 구역을 찾을 수 없습니다.")
    
    zone_service.delete_zone(zone_id)
    return ZoneResponse(status="success", message=f"'{zone_id}' 구역이 성공적으로 삭제되었습니다.", zone_id=zone_id)
