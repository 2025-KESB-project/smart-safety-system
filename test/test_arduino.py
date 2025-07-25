import time
import sys
from pathlib import Path
from loguru import logger

# SpeedController 모듈을 찾기 위해 프로젝트 루트를 시스템 경로에 추가
try:
  project_root = Path(__file__).parent.parent
  sys.path.append(str(project_root))

  from control.speed_controller import SpeedController
  logger.info("SpeedController 모듈을 성공적으로 불러왔습니다.")

except (ImportError, ModuleNotFoundError) as e:
    logger.error(f"모듈 임포트 실패. 이 스크립트를 프로젝트 루트에서 실행하고 있는지 확인하세요. 오류: {e}")
    sys.exit(1)
    
# 아두이노 모터 제어 테스트 함수
def run_test():
  # None -> 자동 찾기, 실패 시 별도 지정 필요
  controller = SpeedController(mock_mode=False, port="COM9")

  # 아두이노 연결 확인
  if not controller.get_port_info():
    logger.error("테스트를 진행할 수 없습니다. 아두이노 연결을 확인해주세요.")
    return

  try:
    logger.info("--- 모터 제어 테스트 시작 ---")

    # 1. 50% 속도로 설정
    logger.info("1. 50% 속도로 설정합니다. (5초간 유지)")
    controller.set_speed(50, "Test: Half speed")
    time.sleep(5)
  
    # 2. 100% 속도로 설정
    logger.info("2. 100% 속도로 설정합니다. (5초간 유지)")
    controller.resume_full_speed("Test: Full speed")
    time.sleep(5)

    # 3. 20% 속도로 설정
    logger.info("3. 20% 속도로 설정합니다. (5초간 유지)")
    controller.set_speed(20, "Test: Low speed")
    time.sleep(5)

    # 4. 모터 정지
    logger.info("4. 모터를 정지합니다.")
    controller.stop_conveyor("Test: Stop")
    time.sleep(2)

  except Exception as e:
    logger.error(f"테스트 중 오류 발생: {e}")

  finally:
    # 5. 연결 종료 (자동으로 모터가 정지됩니다)
    logger.info("--- 테스트 종료. 시리얼 연결을 해제합니다. ---")
    controller.close()

if __name__ == "__main__":
  run_test()