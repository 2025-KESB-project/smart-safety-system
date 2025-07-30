
from typing import Optional, Dict, Any
from loguru import logger

class SystemStateManager:
    """
    시스템의 논리적 상태(활성화 여부, 운전/정비 모드)를 관리하는 중앙 클래스.
    FastAPI의 app.state에 저장되어 싱글톤으로 사용됩니다.
    """
    def __init__(self):
        self.system_is_active: bool = False
        self.operation_mode: Optional[str] = None  # 'AUTOMATIC' or 'MAINTENANCE'
        logger.info("SystemStateManager 초기화됨. 현재 상태: 비활성.")

    def start_automatic_mode(self) -> Dict[str, Any]:
        """'운전 모드'를 시작합니다."""
        self.system_is_active = True
        self.operation_mode = 'AUTOMATIC'
        logger.info("상태 관리자: '운전 모드(AUTOMATIC)'로 전환.")
        return self.get_status()

    def start_maintenance_mode(self) -> Dict[str, Any]:
        """'정비 모드(LOTO)'를 시작합니다."""
        self.system_is_active = True
        self.operation_mode = 'MAINTENANCE'
        logger.info("상태 관리자: '정비 모드(MAINTENANCE)'로 전환.")
        return self.get_status()

    def stop_system_globally(self) -> Dict[str, Any]:
        """모든 작업을 중지하고 시스템을 비활성화합니다."""
        self.system_is_active = False
        self.operation_mode = None
        logger.info("상태 관리자: 시스템 전체 중지됨.")
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """현재 시스템의 논리적 상태를 반환합니다."""
        return {
            "system_is_active": self.system_is_active,
            "operation_mode": self.operation_mode,
        }

    def is_active(self) -> bool:
        """시스템이 현재 활성화 상태인지 확인합니다."""
        return self.system_is_active

    def get_mode(self) -> Optional[str]:
        """현재 설정된 작업 모드를 반환합니다."""
        return self.operation_mode
