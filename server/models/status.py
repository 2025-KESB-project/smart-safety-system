from pydantic import BaseModel, Field

class ServiceStatus(BaseModel):
    """서비스의 상태를 나타내는 모델"""
    status: str = Field(..., description="서비스의 연결 상태 (예: 'connected', 'disconnected')", examples=["connected"])
    details: str | None = Field(None, description="상태에 대한 추가 정보", examples=["Connected to collection 'event_logs'"])
    reason: str | None = Field(None, description="연결 실패 시 원인", examples=["DB service not initialized."])

class SystemStatusResponse(BaseModel):
    """전체 시스템 상태 응답 모델"""
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
