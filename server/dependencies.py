
from fastapi import Request
from server.service_facade import ServiceFacade

def get_service_facade(request: Request) -> ServiceFacade:
    """
    Dependency function to get the ServiceFacade instance from the app state.
    This helps to avoid circular imports.
    """
    return request.app.state.service_facade
