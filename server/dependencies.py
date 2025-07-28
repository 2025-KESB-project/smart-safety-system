from fastapi import Depends, Request
from loguru import logger
from google.cloud.firestore_v1.client import Client

from .services.zone_service import ZoneService
from .services.db_service import DBService
from .service_facade import ServiceFacade

# --- Database Client Dependency ---

def get_db_client(request: Request) -> Client:
    """
    Retrieves the shared Firestore client instance from the app state.
    This dependency ensures that all parts of the app use the same DB client.
    """
    if not hasattr(request.app.state, 'db') or not request.app.state.db:
        logger.error("Firestore client is not available in app.state.")
        raise RuntimeError("Database client not initialized. Check server startup logs.")
    return request.app.state.db

# --- Service Dependencies ---

def get_zone_service(db: Client = Depends(get_db_client)) -> ZoneService:
    """
    Creates and returns an instance of ZoneService, injecting the DB client.
    """
    return ZoneService(db=db)

def get_db_service(db: Client = Depends(get_db_client)) -> DBService:
    """
    Creates and returns an instance of DBService, injecting the DB client.
    """
    return DBService(db=db)

def get_service_facade(request: Request) -> ServiceFacade:
    """
    Retrieves the shared ServiceFacade instance from the app state.
    """
    if not hasattr(request.app.state, 'service_facade') or not request.app.state.service_facade:
        logger.error("ServiceFacade is not available in app.state.")
        raise RuntimeError("ServiceFacade not initialized. Check server startup logs.")
    return request.app.state.service_facade