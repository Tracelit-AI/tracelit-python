from tracelit.configuration import Configuration
from tracelit.instrumentation import reset, shutdown, start
from tracelit.metrics import MetricsFacade
from tracelit.version import VERSION

_config = Configuration()
metrics = MetricsFacade()


def configure(**kwargs):
    global _config
    for key, value in kwargs.items():
        if hasattr(_config, key):
            setattr(_config, key, value)
    return _config


def config():
    return _config


def auto_start(**kwargs):
    configure(**kwargs)
    start(_config)


def tracer():
    from opentelemetry import trace

    return trace.get_tracer(_config.resolved_service_name(), VERSION)


__all__ = [
    "VERSION",
    "configure",
    "config",
    "auto_start",
    "start",
    "shutdown",
    "reset",
    "metrics",
    "tracer",
]
