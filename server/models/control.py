from pydantic import BaseModel, Field

class ControlResponse(BaseModel):
    """제어 API의 응답 모델"""
    status: str = Field(..., description="요청 처리 상태", examples=["success"])
    message: str = Field(..., description="처리 결과에 대한 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Conveyor mode toggled to: ON"
            }
        }

class ConveyorStatusResponse(BaseModel):
    """컨베이어 상태 응답 모델"""
    is_operating: bool = Field(..., description="컨베이어가 현재 작동 중인지 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "is_operating": True
            }
        }
