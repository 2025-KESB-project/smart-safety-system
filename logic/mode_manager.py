from typing import Dict, Any
from loguru import logger

class ModeManager:
    """
    현재 작업장의 상태를 '정형' 또는 '비정형' 작업 모드로 판단합니다.
    """

    def __init__(self, config: Dict = None):
        """
        ModeManager를 초기화합니다.
        
        Args:
            config: 모드 판단 관련 설정
        """
        self.config = config or {}
        self.current_mode = "normal_work"
        logger.info("ModeManager 초기화 완료.")

    def determine_mode(self, is_conveyor_operating: bool) -> str:
        """
        컨베이어 작동 여부를 바탕으로 현재 작업 모드를 결정합니다.

        Args:
            is_conveyor_operating: 컨베이어가 현재 작동 중인지 여부 (True: 작동 중, False: 멈춤)

        Returns:
            현재 작업 모드 문자열 ('operating' 또는 'stopped')
        """
        if is_conveyor_operating:
            self.current_mode = "operating"
            logger.info("작업 모드: 컨베이어 작동 중 (operating)")
        else:
            self.current_mode = "stopped"
            logger.info("작업 모드: 컨베이어 작동 멈춤 (stopped)")
        return self.current_mode