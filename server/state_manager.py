
from typing import Optional, Dict, Any
from loguru import logger
from control.control_facade import ControlFacade

class SystemStateManager:
    """
    시스템의 논리적 상태(모드, 활성화 여부)만을 관리하는 중앙 클래스.
    물리적 장치 제어(ControlFacade)와는 완전히 분리됩니다.
    """
    def __init__(self):
        self.system_is_active: bool = False
        self.operation_mode: Optional[str] = None  # 'AUTOMATIC' or 'MAINTENANCE'
        logger.info("SystemStateManager 초기화됨. (순수 논리 상태 관리)")

    def start_automatic_mode(self):
        """'운전 모드'로 논리적 상태를 전환합니다."""
        self.system_is_active = True
        self.operation_mode = 'AUTOMATIC'
        logger.info("상태 관리자: '운전 모드(AUTOMATIC)'로 전환.")

    def start_maintenance_mode(self):
        """'정비 모드(LOTO)'로 논리적 상태를 전환합니다."""
        self.system_is_active = True
        self.operation_mode = 'MAINTENANCE'
        logger.info("상태 관리자: '정비 모드(MAINTENANCE)'로 전환.")

    def stop_system_globally(self):
        """시스템을 논리적으로 비활성화합니다. 물리적 제어는 호출자가 담당합니다."""
        self.system_is_active = False
        self.operation_mode = None
        logger.info("상태 관리자: 시스템 논리적 상태 중지됨.")

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
