# Changelog

## Unreleased

### Fixes

- Auto-instrumentation no longer logs warnings for missing `opentelemetry-instrumentation-*` packages.
- Skip Django instrumentation when `DJANGO_SETTINGS_MODULE` is not set (e.g. Flask-only processes).

### Documentation

- Explicit per-framework setup guides (Django, Flask, FastAPI, Celery, scripts).
- Clarify `auto_start()` is for Flask/FastAPI/scripts — Django uses `TracelitConfig` only.
- Remove misleading one-line framework bullets; add complete working examples.

## 0.1.0

- Initial Python SDK release.
- Traces, metrics, and logs via OTLP/HTTP.
- Non-blocking error span processor.
- Auto-instrumentation activation using OpenTelemetry bootstrap registry.
- WSGI and ASGI middleware integrations.
