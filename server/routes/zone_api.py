from fastapi import APIRouter, Depends, HTTPException, Body, status
from typing import List
from loguru import logger
from multiprocessing import Queue

from ..services.zone_service import ZoneService
from ..dependencies import get_zone_service, get_command_queue
from ..models.zone import DangerZone, DangerZoneCreate, DangerZoneBase, ZoneResponse, Point

router = APIRouter(
    tags=["위험 구역 (Danger Zones)"]
)

@router.get("", response_model=List[DangerZone], summary="모든 위험 구역 조회")
def get_all_zones(zone_service: ZoneService = Depends(get_zone_service)):
    """설정된 모든 위험 구역의 목록을 조회합니다."""
    try:
        zones_data = zone_service.get_all_zones()
        # Firestore에서 받은 데이터를 Pydantic 모델로 변환합니다.
        # 데이터 형식이 맞지 않으면 여기서 ValidationError가 발생하여 문제를 즉시 알 수 있습니다.
        return [
            DangerZone(
                id=zone['id'],
                name=zone['name'],
                points=[Point(**p) for p in zone.get('points', [])]
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
        id=zone['id'],
        name=zone['name'],
        points=[Point(**p) for p in zone.get('points', [])]
    )

@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED, summary="새로운 위험 구역 생성")
def create_zone(
    zone: DangerZone, 
    zone_service: ZoneService = Depends(get_zone_service),
    command_queue: Queue = Depends(get_command_queue)
):
    """새로운 위험 구역을 생성하고, Vision Worker에게 즉시 업데이트합니다."""
    if zone_service.get_zone(zone.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"ID가 '{zone.id}'인 구역이 이미 존재합니다.")
    
    zone_dict = zone.model_dump()
    zone_service.add_or_update_zone(zone.id, zone_dict)
    
    # Worker에게 최신 Zone 정보 전송
    all_zones = zone_service.get_all_zones()
    command_queue.put({"command": "UPDATE_ZONES", "data": all_zones})
    logger.info(f"Vision Worker에게 업데이트된 Zone 정보 ({len(all_zones)}개) 전송 완료")

    return ZoneResponse(status="success", message=f"'{zone.id}' 구역이 성공적으로 생성되었습니다.", zone_id=zone.id)

@router.put("/{zone_id}", response_model=ZoneResponse, summary="위험 구역 정보 업데이트")
def update_zone(
    zone_id: str,
    zone_data: DangerZoneBase,
    zone_service: ZoneService = Depends(get_zone_service),
    command_queue: Queue = Depends(get_command_queue)
):
    """기존 위험 구역의 이름과 좌표를 업데이트하고, Vision Worker에게 즉시 업데이트합니다."""
    if not zone_service.get_zone(zone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID가 '{zone_id}'인 구역을 찾을 수 없습니다.")
    
    zone_dict = zone_data.model_dump()
    zone_service.add_or_update_zone(zone_id, zone_dict)

    # Worker에게 최신 Zone 정보 전송
    all_zones = zone_service.get_all_zones()
    command_queue.put({"command": "UPDATE_ZONES", "data": all_zones})
    logger.info(f"Vision Worker에게 업데이트된 Zone 정보 ({len(all_zones)}개) 전송 완료")

    return ZoneResponse(status="success", message=f"'{zone_id}' 구역이 성공적으로 업데이트되었습니다.", zone_id=zone_id)

@router.delete("/{zone_id}", response_model=ZoneResponse, summary="위험 구역 삭제")
def delete_zone(
    zone_id: str, 
    zone_service: ZoneService = Depends(get_zone_service),
    command_queue: Queue = Depends(get_command_queue)
):
    """고유 ID를 사용하여 위험 구역을 삭제하고, Vision Worker에게 즉시 업데이트합니다."""
    if not zone_service.get_zone(zone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID가 '{zone_id}'인 구역을 찾을 수 없습니다.")
    
    zone_service.delete_zone(zone_id)

    # Worker에게 최신 Zone 정보 전송
    all_zones = zone_service.get_all_zones()
    command_queue.put({"command": "UPDATE_ZONES", "data": all_zones})
    logger.info(f"Vision Worker에게 업데이트된 Zone 정보 ({len(all_zones)}개) 전송 완료")

    return ZoneResponse(status="success", message=f"'{zone_id}' 구역이 성공적으로 삭제되었습니다.", zone_id=zone_id)
