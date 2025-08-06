from loguru import logger
from typing import List, Dict, Any, Optional

from control.serial_communicator import SerialCommunicator
from control.power_controller import PowerController
from control.speed_controller import SpeedController
from control.alert_controller import AlertController, AlertLevel


class ControlFacade:
    """
    물리적 장치 제어를 위한 통합 인터페이스(Facade).
    의존성 주입 및 상태 캐싱을 통해 효율적이고 안정적인 제어를 제공합니다.
    """
    def __init__(self, communicator: Optional[SerialCommunicator], mock_mode: bool = False, **kwargs):
        self.mock_mode = mock_mode
        self.communicator = communicator

        if not self.mock_mode and self.communicator is None:
            raise ValueError("ControlFacade requires a SerialCommunicator in non-mock mode.")

        self.power_controller = PowerController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.speed_controller = SpeedController(communicator=self.communicator, mock_mode=self.mock_mode)
        self.alert_controller = AlertController(communicator=self.communicator, mock_mode=self.mock_mode)

        # --- 상태 변수(캐시) 초기화 ---
        self.power_state: bool = False
        self.speed_percent: int = 0
        self.alert_level: AlertLevel = AlertLevel.NONE
        
        logger.info(f"ControlFacade 초기화 완료. 모의 모드: {self.mock_mode}")

    async def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        RuleEngine이 결정한 액션 목록을 받아 상태 기반으로 실행합니다.
        캐시된 상태와 비교하여, 상태가 변경될 때만 실제 제어 명령을 내리고 로그를 기록합니다.
        """
        target_power_on = self.power_state
        target_speed = self.speed_percent
        target_alert_level = AlertLevel.NONE

        action_reason = '주기적 확인'
        if actions:
            action_reason = actions[0].get("details", {}).get('reason', '자동 시스템 로직')

            for action in actions:
                action_type = action.get("type", "").upper()
                
                if "POWER_OFF" in action_type or "STOP_POWER" in action_type:
                    target_power_on = False
                elif "POWER_ON" in action_type:
                    target_power_on = True
                
                if "REDUCE_SPEED_50" in action_type:
                    target_speed = 50
                elif "RESUME_FULL_SPEED" in action_type:
                    target_speed = 100
                elif "STOP_CONVEYOR" in action_type or not target_power_on:
                    target_speed = 0

                if "TRIGGER_ALARM_" in action_type:
                    level_str = action_type.replace("TRIGGER_ALARM_", "")
                    try:
                        new_level = AlertLevel[level_str.upper()]
                        if new_level.value > target_alert_level.value:
                           target_alert_level = new_level
                    except KeyError:
                        logger.error(f"알 수 없는 경고 레벨: '{level_str}'")

        # --- 결정된 목표 상태와 캐시된 현재 상태를 비교하여 제어 실행 ---

        if target_power_on != self.power_state:
            logger.info(f"전원 상태 변경: {'ON' if self.power_state else 'OFF'} -> {'ON' if target_power_on else 'OFF'}. 이유: {action_reason}")
            if target_power_on:
                await self.power_controller.power_on(action_reason)
            else:
                await self.power_controller.power_off(action_reason)
            self.power_state = target_power_on

        effective_target_speed = target_speed if self.power_state else 0
        if effective_target_speed != self.speed_percent:
            logger.info(f"속도 상태 변경: {self.speed_percent}% -> {effective_target_speed}%. 이유: {action_reason}")
            if effective_target_speed == 100:
                await self.speed_controller.resume_full_speed(action_reason)
            elif effective_target_speed == 50:
                await self.speed_controller.slow_down_50_percent(action_reason)
            elif effective_target_speed == 0:
                await self.speed_controller.stop_conveyor(action_reason)
            self.speed_percent = effective_target_speed
        
        if target_alert_level != self.alert_level:
            logger.info(f"경고 수준 변경: {self.alert_level.name} -> {target_alert_level.name}. 이유: {action_reason}")
            self.alert_controller.trigger_alert(level=target_alert_level, message=action_reason)
            self.alert_level = target_alert_level

    def get_all_statuses(self) -> dict:
        """Facade에 캐시된 최신 상태를 반환합니다. (동기 함수)"""
        return {
            "conveyor_is_on": self.power_state,
            "conveyor_speed": self.speed_percent,
            "is_alert_on": self.alert_level != AlertLevel.NONE,
            "alert_level": self.alert_level.name
        }

    def release(self):
        """ControlFacade와 모든 하위 컨트롤러의 리소스를 해제합니다."""
        logger.info("ControlFacade 리소스를 해제합니다...")
        if self.communicator:
            self.communicator.close()
        logger.info("ControlFacade 리소스 해제 완료.")
