import logging
import hashlib
from .formatters import ColoredFormatter
from .filters import CorrelationIdFilter
from .key_manager import generate_key
from .crypto import encrypt_message

# ----- Custom file handler for encrypted logs -----
class EncryptedFileHandler(logging.FileHandler):
    def __init__(self, filename, encryption_key, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.encryption_key = encryption_key

    def emit(self, record):
        # Save original message
        original_message = record.getMessage()
        try:
            checksum = hashlib.sha256(original_message.encode('utf-8')).hexdigest()
            encrypted_message = encrypt_message(original_message, self.encryption_key)
            record.msg = f"{checksum}:{encrypted_message}"
        except Exception as e:
            record.msg = f"Encryption failed: {e}"
        super().emit(record)
        # Restore original message for other handlers
        record.msg = original_message

# ----- Custom logger -----
class Logger:
    def __init__(
        self,
        file_name=None,
        log_level="INFO",
        correlation_id=None,
        encrypt_file=False,
        encryption_key=None,
        key_file=None
    ):
        # Create logger
        self.logger = logging.getLogger("custom_logger")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.encryption_key = None
        self.file_handler = None
        self.encrypt_file = encrypt_file

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)

        # Add correlation ID filter if provided
        if correlation_id:
            self.logger.addFilter(CorrelationIdFilter(correlation_id))
    
        # Handle encryption key first
        if encrypt_file:
            self.encryption_key = generate_key(encryption_key, key_file, self)
            self.logger.info(f"Encryption enabled with key from {key_file or 'provided key'}")

        # Add file handler if needed
        if file_name:
            if encrypt_file and self.encryption_key:
                self.file_handler = EncryptedFileHandler(file_name, self.encryption_key)
            else:
                self.file_handler = logging.FileHandler(file_name)
            self.file_handler.setFormatter(logging.Formatter(
                '%(asctime)s>%(levelname)s>%(correlation_id)s>%(message)s'
            ))
            self.logger.addHandler(self.file_handler)

        # Add custom levels for SUCCESS and FAIL if not exist
        if not hasattr(logging, "SUCCESS"):
            logging.SUCCESS = 25
            logging.addLevelName(logging.SUCCESS, "SUCCESS")
        if not hasattr(logging, "FAIL"):
            logging.FAIL = 45
            logging.addLevelName(logging.FAIL, "FAIL")

    # ----- Internal logging method -----
    def _log(self, level, message, extra=None):
        self.logger.log(level, message, extra=extra)

    # ----- Convenience methods -----
    def debug(self, message, extra=None):
        self._log(logging.DEBUG, message, extra)

    def info(self, message, extra=None):
        self._log(logging.INFO, message, extra)

    def warning(self, message, extra=None):
        self._log(logging.WARNING, message, extra)

    def error(self, message, extra=None):
        self._log(logging.ERROR, message, extra)

    def critical(self, message, extra=None):
        self._log(logging.CRITICAL, message, extra)

    def success(self, message, extra=None):
        self._log(logging.SUCCESS, message, extra)

    def fail(self, message, extra=None):
        self._log(logging.FAIL, message, extra)
