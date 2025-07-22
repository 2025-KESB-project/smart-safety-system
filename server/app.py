from fastapi import FastAPI
from pydantic import BaseModel

# 임시 데이터 저장을 위한 변수
# 실제 시스템에서는 main.py의 SmartSafetySystem 인스턴스와 연동 필요
system_status = {
    "mode": "normal",
    "risk_level": "low",
    "power_state": "on",
    "speed": 100
}

app = FastAPI(
    title="Smart Safety System API",
    description="컨베이어 작업 현장 스마트 안전 시스템 API",
    version="1.0.0",
)

class SystemStatusResponse(BaseModel):
    mode: str
    risk_level: str
    power_state: str
    speed: int

@app.get("/status", response_model=SystemStatusResponse, summary="시스템 현재 상태 조회")
def get_system_status():
    """
    시스템의 현재 작업 모드, 위험도, 전원 상태, 속도 등 주요 상태 정보를 반환합니다.
    """
    return system_status

@app.post("/control/mode/{mode_name}", summary="작업 모드 수동 변경")
def set_work_mode(mode_name: str):
    """
    시스템의 작업 모드를 수동으로 변경합니다. (normal, irregular, maintenance 등)
    """
    # 여기에 실제 ModeManager를 제어하는 로직 추가 필요
    system_status["mode"] = mode_name
    return {"message": f"Work mode changed to {mode_name}"}

@app.post("/control/power/{command}", summary="전원 수동 제어")
def control_power(command: str):
    """
    전원을 수동으로 제어합니다. (on, off, emergency_off)
    """
    # 여기에 실제 PowerController를 제어하는 로직 추가 필요
    system_status["power_state"] = command
    return {"message": f"Power command '{command}' executed"}

# FastAPI 서버 실행:
# uvicorn server.app:app --reload
