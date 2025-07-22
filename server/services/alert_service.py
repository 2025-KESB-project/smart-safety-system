from loguru import logger

class AlertService:
    def __init__(self):
        logger.info("AlertService initialized")

    def send_ui_notification(self, details):
        logger.info(f"Sending UI notification: {details}")
        # In a real scenario, this would send data via WebSocket or another mechanism.
        pass
