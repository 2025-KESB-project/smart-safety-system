
from server.services.alert_service import AlertService
from server.services.db_service import DBService

class ServiceFacade:
    def __init__(self, db_service: DBService, alert_service: AlertService):
        """
        Initializes the facade with pre-initialized service instances.
        :param db_service: An instance of DBService.
        :param alert_service: An instance of AlertService.
        """
        # Services are now injected directly
        self.alert_service = alert_service
        self.db_service = db_service
