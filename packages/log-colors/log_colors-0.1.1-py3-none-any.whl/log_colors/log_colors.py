import datetime
import os
import inspect

class log_colors:
    COLORS = {
        "INFO": "\033[94m",   # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m",
    }

    def __init__(self, filename=None, log_file=None):
        if filename is None:
            frame = inspect.stack()[1]
            caller_path = frame.filename
            filename = os.path.basename(caller_path)
        self.name = filename
        self.log_file = log_file
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def _timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _format(self, level, message):
        return f"[{self._timestamp()}] [{self.name}] [{level}] {message}"

    def _write(self, msg):
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(msg + "\n")

    def log(self, level, message):
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]
        formatted = self._format(level, message)
        print(f"{color}{formatted}{reset}")
        self._write(formatted)

    def info(self, msg): self.log("INFO", msg)
    def success(self, msg): self.log("SUCCESS", msg)
    def warning(self, msg): self.log("WARNING", msg)
    def error(self, msg): self.log("ERROR", msg)
