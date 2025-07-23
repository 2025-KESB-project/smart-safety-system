from loguru import logger
from typing import Dict, Any

class LoggerService:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        pass

    def log_info(self, message):
        logger.info(message)

    def log_warning(self, message):
        logger.warning(message)

    def log_error(self, message):
        logger.error(message)