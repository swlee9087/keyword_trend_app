# log_util.py

import os
from datetime import datetime

class Logger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(log_dir, f"log_{timestamp}.txt")

        with open(self.log_file_path, "w", encoding="utf-8") as f:
            f.write(f"[{self._time()}] ========== 로그 시작: {self.log_file_path} ==========\n")

    def _time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def log(self, msg: str):
        line = f"[{self._time()}] {msg}\n"
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(line)

        return line  # optional: 화면 출력에도 쓰고 싶을 경우

# 전역 인스턴스 생성 예시 (app.py 등에서)
# from log_util import Logger
logger = Logger()
# logger.log("이벤트 발생함")
