import os
from server.services.alert_service import AlertService
from server.services.db_service import DBService
# from server.services.logger_service import LoggerService

class ServiceFacade:
    def __init__(self, config: dict = None):
        """
        Initializes and provides access to all backend services.
        :param config: A dictionary containing service-specific configurations.
        """
        if config is None:
            config = {}

        # Initialize services
        self.alert_service = AlertService()
        
        # Initialize DBService with the credential path from config
        credential_path = config.get('db_service', {}).get('firebase_credentials_path')
        if not credential_path or not os.path.exists(credential_path):
            raise FileNotFoundError(
                "Firebase credential file not found. "
                "Please check the path in your configuration."
            )
        self.db_service = DBService(credential_path)


    # You can add methods here to orchestrate multiple services if needed
    # For example:
    # def handle_critical_event(self, data):
    #     self.db_service.log_event(data)
    #     self.alert_service.broadcast(data)
    #     self.logger_service.log(data)