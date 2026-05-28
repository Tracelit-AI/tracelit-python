from tracelit.configuration import Configuration


def test_configuration_defaults():
    config = Configuration()
    assert config.environment
    assert config.endpoint.startswith("https://")


def test_sanitized_resource_attributes():
    config = Configuration(resource_attributes={"ok": 1, "bad": object()})
    safe = config.sanitized_resource_attributes()
    assert safe == {"ok": 1}


def test_valid_errors_without_key(monkeypatch):
    monkeypatch.delenv("TRACELIT_API_KEY", raising=False)
    config = Configuration(api_key=None)
    assert config.valid()
