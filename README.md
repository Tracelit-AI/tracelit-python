# Tracelit Python SDK

Drop-in OpenTelemetry SDK for Python that exports traces, metrics, and logs to Tracelit via OTLP/HTTP.

## Install

```bash
pip install tracelit
```

Install OpenTelemetry instrumentation packages for **your** stack (see each framework section below). Tracelit only instruments libraries whose instrumentation package is installed — missing packages are skipped silently.

```bash
pip install opentelemetry-instrumentation-flask      # Flask apps
pip install opentelemetry-instrumentation-django     # Django apps
pip install opentelemetry-instrumentation-fastapi    # FastAPI apps
pip install opentelemetry-instrumentation-celery     # Celery workers
pip install opentelemetry-instrumentation-redis        # Redis
pip install opentelemetry-instrumentation-requests   # requests HTTP client
```

## Which setup do I use?

| App type | How to initialize Tracelit |
|---|---|
| **Django** | Add `tracelit.integrations.django.TracelitConfig` to `INSTALLED_APPS`. Do **not** call `auto_start()` in `settings.py`. |
| **Flask** | Call `tracelit.auto_start()` in `app.py` before routes run. Expose a module-level `app` object. |
| **FastAPI** | Call `tracelit.auto_start()` in `main.py` before the app serves traffic. |
| **Celery worker** | Call `install_celery_hook()` in `celery.py`. |
| **Script / CLI / batch job** | Call `tracelit.auto_start()` at process startup. |

> There is **no** `tracelit.init()` API.

---

## Django

**1. Add to `settings.py`:**

```python
INSTALLED_APPS = [
    "tracelit.integrations.django.TracelitConfig",  # full path required
    "django.contrib.admin",
    # ...
]
```

**2. Set environment variables** (`.env`, deployment config, etc.):

```bash
TRACELIT_API_KEY=your-api-key
TRACELIT_SERVICE_NAME=payments-api
TRACELIT_ENVIRONMENT=production
TRACELIT_ENDPOINT=https://ingest.tracelit.app
```

**3. Install Django instrumentation:**

```bash
pip install opentelemetry-instrumentation-django
```

**4. Restart Django** (`runserver`, gunicorn, uvicorn, etc.).

Tracelit starts automatically in `AppConfig.ready()` after Django is configured.

### python-decouple / django-environ

Bridge secrets into `os.environ` **before** `INSTALLED_APPS`:

```python
import os
from decouple import config

os.environ.setdefault("TRACELIT_API_KEY", config("TRACELIT_API_KEY"))
os.environ.setdefault("TRACELIT_SERVICE_NAME", config("TRACELIT_SERVICE_NAME", default="backend"))
os.environ.setdefault("TRACELIT_ENVIRONMENT", config("TRACELIT_ENVIRONMENT", default="production"))
```

> **Do not** call `tracelit.auto_start()` at the top of `settings.py`.

### Celery (Django projects with background workers)

In `celery.py`:

```python
from tracelit.integrations.celery import install_celery_hook

install_celery_hook()
```

```bash
pip install opentelemetry-instrumentation-celery
```

---

## Flask

**1. `app.py` — complete working example:**

```python
import os

import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="my-flask-app",
    environment=os.getenv("FLASK_ENV", "production"),
)

from flask import Flask
from tracelit.integrations.wsgi import TracelitWSGIMiddleware

app = Flask(__name__)
app.wsgi_app = TracelitWSGIMiddleware(app.wsgi_app)


@app.get("/")
def home():
    return "ok"
```

**2. Install Flask instrumentation:**

```bash
pip install opentelemetry-instrumentation-flask opentelemetry-instrumentation-wsgi
```

**3. Run:**

```bash
export TRACELIT_API_KEY=your-api-key
FLASK_APP=app.py flask run
```

`FLASK_APP=app.py` requires a module-level variable named `app`. If your factory is named differently, use `FLASK_APP=app:create_app` instead.

`TracelitWSGIMiddleware` adds HTTP request metrics. Flask route tracing comes from `opentelemetry-instrumentation-flask`.

---

## FastAPI

**1. `main.py` — complete working example:**

```python
import os

import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="my-api",
    environment=os.getenv("ENV", "production"),
)

from fastapi import FastAPI
from tracelit.integrations.asgi import TracelitASGIMiddleware

app = FastAPI()
app = TracelitASGIMiddleware(app)


@app.get("/")
def home():
    return {"ok": True}
```

**2. Install FastAPI instrumentation:**

```bash
pip install opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-asgi
```

**3. Run with uvicorn:**

```bash
export TRACELIT_API_KEY=your-api-key
uvicorn main:app
```

---

## Scripts and batch jobs (no web framework)

Use `tracelit.auto_start()` at the top of your entry point. This is for CLIs, cron jobs, and one-off scripts — **not** for Django (use `TracelitConfig` instead).

```python
import os
import tracelit

tracelit.auto_start(
    api_key=os.environ["TRACELIT_API_KEY"],
    service_name="nightly-report",
    environment=os.getenv("ENV", "production"),
)

with tracelit.tracer().start_as_current_span("generate-report"):
    # your logic here
    pass
```

Or rely entirely on environment variables:

```python
import tracelit

tracelit.auto_start()
```

---

## Manual spans and metrics

```python
import tracelit

with tracelit.tracer().start_as_current_span("process-order"):
    tracelit.metrics.counter("orders.processed").add(1)
```

---

## Configuration

| Option | Env var | Default |
|---|---|---|
| api_key | `TRACELIT_API_KEY` | required |
| service_name | `TRACELIT_SERVICE_NAME` | `unknown-service` |
| environment | `TRACELIT_ENVIRONMENT` | `production` |
| endpoint | `TRACELIT_ENDPOINT` | `https://ingest.tracelit.app` |
| sample_rate | `TRACELIT_SAMPLE_RATE` | `1.0` |
| enabled | `TRACELIT_ENABLED` | `true` |

Set `TRACELIT_ENABLED=false` in tests to disable telemetry with no code changes.

## Behavior guarantees

- Non-blocking span export with async error-span queue
- Never raises setup or exporter failures into customer code
- Graceful shutdown flush at process exit
- Error spans are always exported, even when sampling is below `1.0`
- Missing instrumentation packages are skipped silently (no startup warning spam)
