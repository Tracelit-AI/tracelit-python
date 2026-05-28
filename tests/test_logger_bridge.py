import logging

from tracelit.logger_bridge import TracelitLoggingHandler


class DummyLogger:
    def __init__(self):
        self.records = []

    def emit(self, **kwargs):
        self.records.append(kwargs)


class DummyProvider:
    def __init__(self):
        self.logger = DummyLogger()

    def get_logger(self, _name):
        return self.logger


def test_logging_handler_emits():
    handler = TracelitLoggingHandler(DummyProvider())
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", args=(), exc_info=None)
    handler.emit(record)
    assert handler._otel_logger.records
