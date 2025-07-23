

import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime, timezone
from loguru import logger

class DBService:
    def __init__(self, credential_path):
        """
        Initializes the Firebase Admin SDK and Firestore client.
        :param credential_path: Path to the Firebase service account key file.
        """
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(credential_path)
                firebase_admin.initialize_app(cred)
                logger.success("Firebase Admin SDK initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Firebase Admin SDK: {e}")
                raise
        
        self.db = firestore.client()
        logger.success("Firestore client created successfully.")

    def get_status(self):
        """
        Checks the status of the Firestore client.
        """
        if self.db:
            return {"status": "connected"}
        else:
            return {"status": "disconnected", "reason": "Firestore client not initialized."}

    def log_event(self, event_type: str, risk_level: str, details: dict):
        """
        Logs an event to the 'event_logs' collection in Firestore.

        :param event_type: The type of the event (e.g., 'LOG_LOTO_ACTIVE').
        :param risk_level: The risk level associated with the event.
        :param details: A dictionary containing detailed information about the event.
        """
        try:
            doc_ref = self.db.collection('event_logs').document()
            event_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': event_type,
                'risk_level': risk_level,
                'details': details
            }
            doc_ref.set(event_data)
            # 로그 레벨을 INFO로 변경하여 일반적인 성공 로그로 처리
            logger.info(f"Successfully logged event: {event_type}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error logging event to Firestore: {e}")
            return None

    def get_events(self, limit: int = 50):
        """
        Retrieves the latest events from the 'event_logs' collection.

        :param limit: The maximum number of events to retrieve.
        :return: A list of event documents, or an empty list in case of an error.
        """
        try:
            docs = self.db.collection('event_logs').order_by(
                'timestamp', direction=firestore.Query.DESCENDING
            ).limit(limit).stream()
            
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                events.append(event_data)
            
            logger.debug(f"Successfully retrieved {len(events)} events.")
            return events
        except Exception as e:
            logger.error(f"Error retrieving events from Firestore: {e}")
            return []

# Example of how to get the credential path dynamically
# This assumes the script is run from the project root.
# In our actual app, the path will be managed by the ServiceFacade.
def get_credential_path():
    return os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'firebase_credential.json')

if __name__ == '__main__':
    # Example usage for testing
    try:
        # 테스트 스크립트에서는 logger를 직접 설정해줘야 출력을 볼 수 있습니다.
        from loguru import logger
        import sys
        logger.add(sys.stderr, level="INFO")

        cred_path = get_credential_path()
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase credential file not found at: {cred_path}")
            
        db_service = DBService(credential_path=cred_path)
        
        # Example event
        test_event_details = {
            "reason": "test_event_from_script",
            "risk_details": [
                {"type": "test", "description": "This is a test event."}
            ]
        }
        
        logger.info("\nLogging a test event...")
        event_id = db_service.log_event(
            event_type="LOG_TEST_EVENT",
            risk_level="info",
            details=test_event_details
        )
        
        if event_id:
            logger.info(f"Test event logged with document ID: {event_id}")
        else:
            logger.error("Failed to log test event.")
            
    except Exception as e:
        logger.error(f"An error occurred during the test run: {e}")

