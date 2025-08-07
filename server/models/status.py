from pydantic import BaseModel, Field
from typing import Optional


class ServiceStatus(BaseModel):
    """서비스의 상태를 나타내는 모델"""
    status: str = Field(..., description="서비스의 연결 상태 (예: 'connected', 'disconnected')", examples=["connected"])
    details: str | None = Field(None, description="상태에 대한 추가 정보", examples=["Connected to collection 'event_logs'"])
    reason: str | None = Field(None, description="연결 실패 시 원인", examples=["DB service not initialized."])

class ConfirmationResponse(BaseModel):
    """2차 확인이 필요할 때의 응답 모델"""
    confirmation_required: bool = Field(True, description="2차 확인 필요 여부")
    message: str = Field(..., description="사용자에게 보여줄 확인 메시지")

class SystemStatusResponse(BaseModel):
    """전체 시스템 상태 응답 모델"""
    system_is_active: bool = Field(..., description="시스템의 논리적 활성화 여부")
    operation_mode: Optional[str] = Field(None, description="현재 작업 모드 (AUTOMATIC, MAINTENANCE)")
    conveyor_is_on: bool = Field(..., description="컨베이어의 실제 전원 상태")
    conveyor_speed: int = Field(..., description="컨베이어의 현재 속도")
    # 여기에 다른 물리적 상태들을 추가할 수 있습니다.
    database_service: ServiceStatus = Field(..., description="데이터베이스 서비스의 상태")
    background_worker_alive: bool = Field(..., description="백그라운드 워커 스레드의 활성화 여부")

class LogicalStatusResponse(BaseModel):
    """물리적 상태를 제외한 논리적 시스템 상태 응답 모델"""
    system_is_active: bool = Field(..., description="시스템의 논리적 활성화 여부")
    operation_mode: Optional[str] = Field(None, description="현재 작업 모드 (AUTOMATIC, MAINTENANCE)")
    database_service: ServiceStatus = Field(..., description="데이터베이스 서비스의 상태")
    background_worker_alive: bool = Field(..., description="백그라운드 워커 스레드의 활성화 여부")

    class Config:
        # FastAPI 문서에 보여줄 예시 데이터
        json_schema_extra = {
            "example": {
                "database_service": {
                    "status": "connected",
                    "details": "Connected to collection 'event_logs'"
                },
                "background_worker_alive": True
            }
        }
