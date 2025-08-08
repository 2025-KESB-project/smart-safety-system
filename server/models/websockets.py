from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Dict, Any

class AlertMessage(BaseModel):
    """실시간 위험 경보를 위한 웹소켓 메시지 모델"""
    type: str = Field(default="SYSTEM_ALERT", description="메시지 유형", examples=["SYSTEM_ALERT"])
    level: str = Field(..., description="위험 수준 (예: 'high', 'critical')", examples=["critical"])
    message: str = Field(..., description="경보 메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.now, description="이벤트 발생 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "SYSTEM_ALERT",
                "level": "critical",
                "message": "사람 넘어짐 감지! 시스템을 즉시 정지합니다.",
                "timestamp": "2025-07-28T14:30:00.123Z"
            }
        }

class LogMessage(BaseModel):
    """실시간 로그 스트리밍을 위한 웹소켓 메시지 모델"""
    event_type: str = Field(..., description="발생한 이벤트의 유형", examples=["LOG_HIGH_RISK"])
    risk_level: str | None = Field(None, description="관련된 위험 수준", examples=["high"])
    operation_mode: str | None = Field(None, description="이벤트 발생 시점의 시스템 동작 모드", examples=["AUTOMATIC"])
    details: Dict[str, Any] = Field(default_factory=dict, description="이벤트 관련 상세 정보")
    timestamp: str = Field(..., description="이벤트 발생 시간 (ISO 8601 형식)", examples=["2025-07-28T15:00:00.123456"])

    @field_validator('timestamp')
    def validate_timestamp(cls, v):
        """타임스탬프가 유효한 ISO 8601 형식인지 검증합니다."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            raise ValueError("Timestamp must be a valid ISO 8601 string")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "LOG_HIGH_RISK",
                "risk_level": "high",
                "details": {
                    "reason": "person_in_danger_zone",
                    "detected_persons": 1
                },
                "timestamp": "2025-07-28T15:00:00.123456"
            }
        }