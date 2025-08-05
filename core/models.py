from pydantic import BaseModel, Field
from typing import List, Optional

class Point(BaseModel):
    """x, y 좌표를 나타내는 단일 포인트 모델"""
    x: int = Field(..., description="포인트의 x 좌표")
    y: int = Field(..., description="포인트의 y 좌표")

class DangerZoneBase(BaseModel):
    """위험 구역의 공통 속성을 정의하는 기본 모델"""
    name: str = Field(..., description="사람이 읽을 수 있는 구역의 이름", examples=["1번 컨베이어 벨트 구역"])
    points: List[Point] = Field(..., description="구역의 다각형을 정의하는 포인트의 리스트")

class DangerZoneCreate(DangerZoneBase):
    """새로운 위험 구역을 생성할 때 사용하는 모델 (ID는 포함되지 않음)"""
    pass

class DangerZone(DangerZoneBase):
    """데이터베이스에 저장된 위험 구역을 나타내는 모델 (ID 포함)"""
    id: str = Field(..., description="구역의 고유 식별자", examples=["zone_01"])

    class Config:
        # 이 설정을 통해 딕셔너리 뿐만 아니라 객체 속성으로도 모델을 생성할 수 있습니다.
        from_attributes = True

class ZoneResponse(BaseModel):
    """구역 관련 작업에 대한 표준 응답 모델"""
    status: str = Field(..., description="작업 처리 상태", examples=["success"])
    message: str = Field(..., description="처리 결과에 대한 설명 메시지")
    zone_id: Optional[str] = Field(None, description="해당하는 구역의 ID (해당하는 경우)", examples=["zone_01"])
