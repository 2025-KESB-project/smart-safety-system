import os
from pathlib import Path
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore

# This is a global variable to hold the single client instance per process.
_db_client = None

def get_db_client() -> firestore.Client:
    """
    Initializes and returns a singleton Firestore client for the current process.
    This function uses lazy initialization to be compatible with uvicorn's reloader,
    which uses fork(). gRPC (used by Firestore) is not fork-safe, so we must
    initialize the client *after* the fork has occurred, which this function achieves.
    """
    global _db_client
    if _db_client is not None:
        return _db_client

    # Use the process ID in the app name to ensure uniqueness in reload scenarios.
    app_name = f"firestore-app-{os.getpid()}"
    logger.info(f"Process(PID: {os.getpid()}) initializing new Firestore client for app '{app_name}'...")

    try:
        # Use environment variable to detect emulator vs. production.
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            logger.warning("FIRESTORE_EMULATOR_HOST detected. Using Firestore emulator.")
            cred = credentials.AnonymousCredentials()
            project_id = "smart-safety-system-emul"
        else:
            logger.info("Connecting to production Firestore.")
            cred_path = str(Path(__file__).parent.parent / "config" / "firebase_credential.json")
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase credential file not found: {cred_path}")
            cred = credentials.Certificate(cred_path)
            project_id = None  # Let the credential file determine the project ID.

        # Check if the app is already initialized to prevent errors during hot-reloads.
        if not any(app.name == app_name for app in firebase_admin._apps.values()):
            firebase_admin.initialize_app(cred, name=app_name, options={"projectId": project_id} if project_id else {})
        
        app_instance = firebase_admin.get_app(name=app_name)
        _db_client = firestore.client(app=app_instance)
        
        logger.success(f"Process(PID: {os.getpid()}) Firestore client initialized successfully.")
        return _db_client

    except Exception as e:
        logger.critical(f"Fatal error during Firestore initialization: {e}", exc_info=True)
        raise RuntimeError("Failed to initialize Firestore client") from e
