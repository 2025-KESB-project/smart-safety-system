
from typing import Optional, Dict, Any
from loguru import logger

class SystemStateManager:
    """
    시스템의 논리적 상태(모드, 활성화 여부, 잠금 상태)만을 관리하는 중앙 클래스.
    물리적 장치 제어와는 완전히 분리됩니다.
    """
    def __init__(self):
        self.system_is_active: bool = False
        self.operation_mode: Optional[str] = None  # 'AUTOMATIC' or 'MAINTENANCE'
        self.is_locked: bool = False  # 하드웨어 비상 정지 등 심각한 이벤트 발생 시 True
        logger.info("SystemStateManager 초기화됨. (순수 논리 상태 관리)")

    def start_automatic_mode(self):
        """'운전 모드'로 논리적 상태를 전환합니다."""
        if self.is_locked:
            logger.warning("시스템이 잠금 상태(LOCKED)이므로 운전 모드로 전환할 수 없습니다.")
            return
        self.system_is_active = True
        self.operation_mode = 'AUTOMATIC'
        logger.info("상태 관리자: '운전 모드(AUTOMATIC)'로 전환.")

    def start_maintenance_mode(self):
        """'정비 모드(LOTO)'로 논리적 상태를 전환합니다."""
        if self.is_locked:
            logger.warning("시스템이 잠금 상태(LOCKED)이므로 정비 모드로 전환할 수 없습니다.")
            return
        self.system_is_active = True
        self.operation_mode = 'MAINTENANCE'
        logger.info("상태 관리자: '정비 모드(MAINTENANCE)'로 전환.")

    def stop_system_globally(self):
        """시스템을 논리적으로 비활성화합니다. 잠금 상태는 유지됩니다."""
        self.system_is_active = False
        self.operation_mode = None
        logger.info("상태 관리자: 시스템 논리적 상태 중지됨.")

    def lock_system(self, reason: str):
        """시스템을 잠금(LOCKED) 상태로 전환합니다."""
        if not self.is_locked:
            self.is_locked = True
            self.system_is_active = False # 잠금 상태에서는 시스템을 비활성화
            logger.critical(f"!!! 시스템 잠금(LOCKED) !!! 이유: {reason}")

    def reset_system(self):
        """잠금(LOCKED) 상태를 해제하고 시스템을 초기 상태로 되돌립니다."""
        if self.is_locked:
            self.is_locked = False
            self.system_is_active = False
            self.operation_mode = None
            logger.info("시스템 잠금(LOCKED) 상태가 관리자에 의해 해제되었습니다. 시스템은 현재 비활성 상태입니다.")
        else:
            logger.info("시스템이 잠금 상태가 아니므로 리셋할 필요가 없습니다.")

    def get_status(self) -> Dict[str, Any]:
        """현재 시스템의 논리적 상태를 반환합니다."""
        return {
            "system_is_active": self.system_is_active,
            "operation_mode": self.operation_mode,
            "is_locked": self.is_locked,
        }

    def is_active(self) -> bool:
        """시스템이 현재 활성화 상태인지 확인합니다. 잠겨있으면 항상 False입니다."""
        if self.is_locked:
            return False
        return self.system_is_active
    
    def is_locked_status(self) -> bool:
        """현재 시스템의 잠금 상태를 반환합니다."""
        return self.is_locked

    def get_mode(self) -> Optional[str]:
        """현재 설정된 작업 모드를 반환합니다."""
        return self.operation_mode
