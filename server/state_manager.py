
from typing import Optional, Dict, Any
from loguru import logger
from control.control_facade import ControlFacade

class SystemStateManager:
    """
    시스템의 논리적/물리적 상태를 모두 총괄하는 중앙 클래스.
    FastAPI의 app.state에 저장되어 싱글톤으로 사용됩니다.
    """
    def __init__(self, control_facade: ControlFacade):
        self.system_is_active: bool = False
        self.operation_mode: Optional[str] = None  # 'AUTOMATIC' or 'MAINTENANCE'
        self.control_facade = control_facade
        logger.info("SystemStateManager 초기화됨. (ControlFacade 주입 완료)")

    def start_automatic_mode(self):
        """'운전 모드'를 시작합니다."""
        self.system_is_active = True
        self.operation_mode = 'AUTOMATIC'
        logger.info("상태 관리자: '운전 모드(AUTOMATIC)'로 전환.")

    def start_maintenance_mode(self):
        """'정비 모드(LOTO)'를 시작합니다."""
        self.system_is_active = True
        self.operation_mode = 'MAINTENANCE'
        logger.info("상태 관리자: '정비 모드(MAINTENANCE)'로 전환.")

    def stop_system_globally(self):
        """모든 작업을 중지하고 시스템을 비활성화합니다."""
        self.system_is_active = False
        self.operation_mode = None
        logger.info("상태 관리자: 시스템 전체 중지됨.")

    def get_status(self) -> Dict[str, Any]:
        """시스템의 논리적 상태와 물리적 상태를 종합하여 반환합니다."""
        logical_status = {
            "system_is_active": self.system_is_active,
            "operation_mode": self.operation_mode,
        }
        # ControlFacade를 통해 모든 물리적 장치의 상태를 한 번에 가져옵니다.
        physical_status = self.control_facade.get_all_statuses()
        
        # 두 상태 딕셔너리를 결합하여 반환
        return {**logical_status, **physical_status}

    def is_active(self) -> bool:
        """시스템이 현재 활성화 상태인지 확인합니다."""
        return self.system_is_active

    def get_mode(self) -> Optional[str]:
        """현재 설정된 작업 모드를 반환합니다."""
        return self.operation_mode
