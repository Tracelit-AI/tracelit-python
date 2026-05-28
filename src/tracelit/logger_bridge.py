from __future__ import annotations

import contextvars
import logging
from typing import Any

from opentelemetry._logs import SeverityNumber

_in_emit = contextvars.ContextVar("tracelit_in_emit", default=False)


def _severity(level: int) -> SeverityNumber:
    if level >= logging.CRITICAL:
        return SeverityNumber.FATAL
    if level >= logging.ERROR:
        return SeverityNumber.ERROR
    if level >= logging.WARNING:
        return SeverityNumber.WARN
    if level >= logging.INFO:
        return SeverityNumber.INFO
    return SeverityNumber.DEBUG


class TracelitLoggingHandler(logging.Handler):
    def __init__(self, logger_provider: Any) -> None:
        super().__init__()
        self._otel_logger = logger_provider.get_logger("tracelit")

    def emit(self, record: logging.LogRecord) -> None:
        if _in_emit.get():
            return
        token = _in_emit.set(True)
        try:
            body = self.format(record) if self.formatter else record.getMessage()
            self._otel_logger.emit(
                severity_number=_severity(record.levelno),
                severity_text=record.levelname,
                body=body,
                attributes={"logger.name": record.name},
            )
        except Exception:
            return
        finally:
            _in_emit.reset(token)


def install_logging_bridge(logger_provider: Any) -> None:
    root = logging.getLogger()
    if any(isinstance(h, TracelitLoggingHandler) for h in root.handlers):
        return
    root.addHandler(TracelitLoggingHandler(logger_provider))
