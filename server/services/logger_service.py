import json
import time
from pathlib import Path
from typing import Dict, Any

class LoggerService:
    """시스템의 주요 이벤트를 파일에 로깅하는 서비스"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"events_{time.strftime('%Y%m%d')}.log"
        print(f"LoggerService 초기화. 로그 파일: {self.log_file}")

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        이벤트를 로그 파일에 기록합니다.

        Args:
            event_type: 이벤트 유형 (e.g., 'risk_assessment', 'mode_change')
            data: 로깅할 데이터
        """
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"로그 기록 실패: {e}")

# 사용 예시
if __name__ == '__main__':
    logger = LoggerService()
    logger.log_event("system_start", {"message": "Smart Safety System이 시작되었습니다."})
    logger.log_event("risk_detected", {"level": "high", "reason": "Person in danger zone"})
    logger.log_event("mode_change", {"from": "normal", "to": "irregular"})

