# Tracelit Python SDK

Drop-in OpenTelemetry SDK for Python that exports traces, metrics, and logs to Tracelit via OTLP/HTTP.

## Install

```bash
pip install tracelit
```

Optional extras:

```bash
pip install "tracelit[web]"
pip install "tracelit[db]"
pip install "tracelit[all]"
```

## Quick start

```python
import tracelit

tracelit.auto_start(
    api_key="YOUR_KEY",
    service_name="payments-api",
    environment="production",
)
```

## Frameworks

- Django: add `tracelit.integrations.django.TracelitConfig` to `INSTALLED_APPS`
- FastAPI/Starlette/Sanic/Quart: wrap app with `TracelitASGIMiddleware`
- Flask/Pyramid/Bottle/CherryPy: wrap app with `TracelitWSGIMiddleware`
- Celery: call `install_celery_hook()` from `tracelit.integrations.celery`

## Behavior guarantees

- Non-blocking span export with async error-span queue
- Never raises setup or exporter failures into customer code
- Graceful shutdown flush at process exit
- `TRACELIT_ENABLED=false` disables telemetry

## Configuration

| Option | Env var | Default |
|---|---|---|
| api_key | TRACELIT_API_KEY | required |
| service_name | TRACELIT_SERVICE_NAME | unknown-service |
| environment | TRACELIT_ENVIRONMENT | production |
| endpoint | TRACELIT_ENDPOINT | https://ingest.tracelit.app |
| sample_rate | TRACELIT_SAMPLE_RATE | 1.0 |
| enabled | TRACELIT_ENABLED | true |
