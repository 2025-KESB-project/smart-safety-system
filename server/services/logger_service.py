from loguru import logger

class LoggerService:
    def __init__(self):
        logger.info("LoggerService initialized")

    def log_info(self, message):
        logger.info(message)

    def log_warning(self, message):
        logger.warning(message)

    def log_error(self, message):
        logger.error(message)