import logging
import json
from colorama import init, Fore, Style

init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Formatter for colored console output."""
    LEVEL_COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.WHITE,
        'SUCCESS': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'FAIL': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def __init__(self):
        super().__init__("%(message)s")

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelname, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

class JsonFormatter(logging.Formatter):
    """Formatter for JSON output."""
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record, "%Y/%m/%d %H:%M:%S,%f"),
            'level': record.levelname,
            'correlation_id': getattr(record, 'correlation_id', 'none'),
            'message': record.getMessage(),
        }
        return json.dumps(log_entry)