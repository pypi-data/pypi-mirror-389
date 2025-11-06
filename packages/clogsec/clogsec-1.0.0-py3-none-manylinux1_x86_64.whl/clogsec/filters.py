import logging
import uuid

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    def __init__(self, correlation_id=None):
        super().__init__()
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def filter(self, record):
        record.correlation_id = self.correlation_id
        return True