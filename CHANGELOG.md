# Changelog

## Unreleased

### Documentation

- Correct Django setup: use `tracelit.integrations.django.TracelitConfig` in `INSTALLED_APPS` (not `tracelit.integrations.django` alone).
- Clarify there is no `tracelit.init()` API — use `tracelit.auto_start()`.
- Document that OpenTelemetry instrumentation packages must be installed separately.
- Add framework guides for Django, Flask, FastAPI, Celery, and python-decouple env bridging.
- Add Mintlify docs page at `/sdk/python`.

## 0.1.0

- Initial Python SDK release.
- Traces, metrics, and logs via OTLP/HTTP.
- Non-blocking error span processor.
- Auto-instrumentation activation using OpenTelemetry bootstrap registry.
- WSGI and ASGI middleware integrations.
