
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

# 순환 참조를 피하기 위해 app.py 대신 dependencies.py에서 의존성을 가져옵니다.
from server.dependencies import get_service_facade
from server.service_facade import ServiceFacade

event_router = APIRouter()

@event_router.get("/events", 
            response_model=List[Dict[str, Any]],
            summary="Get Latest Safety Events",
            description="Retrieves a list of the most recent safety event logs from Firestore, sorted by timestamp in descending order.")
async def get_latest_events(
    limit: int = 50,
    service_facade: ServiceFacade = Depends(get_service_facade)
):
    """
    Fetches the latest safety events recorded by the system.
    
    - **limit**: The maximum number of events to return. Defaults to 50.
    """
    try:
        events = service_facade.db_service.get_events(limit=limit)
        return events
    except Exception as e:
        # In a real application, you might want more specific error handling
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching events: {e}"
        )

