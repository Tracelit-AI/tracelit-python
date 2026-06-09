# Tracelit Python SDK

Drop-in OpenTelemetry SDK for Python that exports traces, metrics, and logs to Tracelit via OTLP/HTTP.

## Install

```bash
pip install tracelit
```

The base package includes the Tracelit exporter and auto-instrumentation bootstrap. **Install OpenTelemetry instrumentation packages for the libraries you use** (Django, Flask, Redis, Celery, etc.) — see [Instrumentation packages](#instrumentation-packages) below.

Optional extras (install only what you need):

```bash
pip install "tracelit[web]"      # Django, Flask, FastAPI, ASGI/WSGI
pip install "tracelit[db]"       # SQLAlchemy, psycopg2, pymysql, redis, ...
pip install "tracelit[workers]"  # Celery
pip install "tracelit[http]"     # requests, httpx, urllib3
```

If an extra fails to resolve (some contrib packages are not published for every Python version), install the individual `opentelemetry-instrumentation-*` packages you need instead.

## Quick start (scripts / generic apps)

```python
import os
import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="payments-api",
    environment=os.getenv("ENV", "production"),
)
```

Or rely entirely on environment variables and call:

```python
import tracelit

tracelit.auto_start()
```

## Framework integration

> **There is no `tracelit.init()` API.** Use `tracelit.auto_start()` or the framework hooks below.

### Django

Add the app config to `INSTALLED_APPS` (ideally first). Tracelit starts automatically in `AppConfig.ready()` **after** Django is configured.

```python
# settings.py
INSTALLED_APPS = [
    "tracelit.integrations.django.TracelitConfig",  # not "tracelit.integrations.django"
    "django.contrib.admin",
    # ...
]
```

Set environment variables (`.env`, deployment config, etc.):

```bash
TRACELIT_API_KEY=your-api-key
TRACELIT_SERVICE_NAME=payments-api
TRACELIT_ENVIRONMENT=production
TRACELIT_ENDPOINT=https://ingest.tracelit.app
```

> **Do not** call `tracelit.auto_start()` at the top of `settings.py`. Settings load before Django is fully initialized and framework instrumentation will fail or silently no-op.

If you load secrets with `python-decouple` or `django-environ`, bridge them into `os.environ` **before** `INSTALLED_APPS`:

```python
import os
from decouple import config

os.environ.setdefault("TRACELIT_API_KEY", config("TRACELIT_API_KEY"))
os.environ.setdefault("TRACELIT_SERVICE_NAME", config("TRACELIT_SERVICE_NAME", default="backend"))
os.environ.setdefault("TRACELIT_ENVIRONMENT", config("TRACELIT_ENVIRONMENT", default="production"))
```

Install Django instrumentation:

```bash
pip install opentelemetry-instrumentation-django
```

### Flask / WSGI apps

Call `auto_start()` before handling requests, then optionally wrap the WSGI app for HTTP metrics:

```python
import os
import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="my-flask-app",
)

from flask import Flask
from tracelit.integrations.wsgi import TracelitWSGIMiddleware

app = Flask(__name__)
app.wsgi_app = TracelitWSGIMiddleware(app.wsgi_app)
```

```bash
pip install opentelemetry-instrumentation-flask opentelemetry-instrumentation-wsgi
```

### FastAPI / Starlette / ASGI apps

```python
import os
import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="my-api",
)

from fastapi import FastAPI
from tracelit.integrations.asgi import TracelitASGIMiddleware

app = FastAPI()
app = TracelitASGIMiddleware(app)
```

```bash
pip install opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-asgi
```

### Celery workers

Web process instrumentation does **not** cover Celery workers. Add this to your `celery.py`:

```python
from tracelit.integrations.celery import install_celery_hook

install_celery_hook()
```

```bash
pip install opentelemetry-instrumentation-celery
```

Restart workers after installing instrumentation packages.

## Instrumentation packages

On startup, Tracelit attempts to instrument installed libraries. If a package is missing, you will see warnings like:

```
[Tracelit] failed to instrument opentelemetry-instrumentation-django: No module named 'opentelemetry.instrumentation.django'
```

These are **warnings, not crashes** — but without the matching instrumentation package you will not get traces for that library.

| Your stack | Install |
|---|---|
| Django | `opentelemetry-instrumentation-django` |
| Flask | `opentelemetry-instrumentation-flask` |
| FastAPI | `opentelemetry-instrumentation-fastapi` |
| PostgreSQL (psycopg2) | `opentelemetry-instrumentation-psycopg2` |
| MySQL | `opentelemetry-instrumentation-pymysql` or `opentelemetry-instrumentation-mysqlclient` |
| Redis | `opentelemetry-instrumentation-redis` |
| Celery | `opentelemetry-instrumentation-celery` |
| HTTP clients | `opentelemetry-instrumentation-requests`, `opentelemetry-instrumentation-httpx` |

Disable specific instrumentations:

```bash
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=sqlite3,asyncio
```

## Manual spans and metrics

```python
import tracelit

with tracelit.tracer().start_as_current_span("process-order"):
    tracelit.metrics.counter("orders.processed").add(1)
```

## Behavior guarantees

- Non-blocking span export with async error-span queue
- Never raises setup or exporter failures into customer code
- Graceful shutdown flush at process exit
- `TRACELIT_ENABLED=false` disables telemetry
- Error spans are always exported, even when sampling is below `1.0`

## Configuration

| Option | Env var | Default |
|---|---|---|
| api_key | `TRACELIT_API_KEY` | required |
| service_name | `TRACELIT_SERVICE_NAME` | `unknown-service` |
| environment | `TRACELIT_ENVIRONMENT` | `production` |
| endpoint | `TRACELIT_ENDPOINT` | `https://ingest.tracelit.app` |
| sample_rate | `TRACELIT_SAMPLE_RATE` | `1.0` |
| enabled | `TRACELIT_ENABLED` | `true` |
