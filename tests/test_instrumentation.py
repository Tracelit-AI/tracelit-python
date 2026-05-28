from tracelit.configuration import Configuration
from tracelit.instrumentation import reset, start


def test_start_disabled():
    reset()
    start(Configuration(enabled=False, api_key="x", service_name="svc"))


def test_start_with_valid_config():
    reset()
    start(Configuration(api_key="x", service_name="svc"))
