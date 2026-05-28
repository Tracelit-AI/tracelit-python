from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Any


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() != "false"


@dataclass
class Configuration:
    api_key: str | None = field(default_factory=lambda: os.getenv("TRACELIT_API_KEY"))
    service_name: str | None = field(default_factory=lambda: os.getenv("TRACELIT_SERVICE_NAME"))
    environment: str = field(default_factory=lambda: os.getenv("TRACELIT_ENVIRONMENT", "production"))
    endpoint: str = field(default_factory=lambda: os.getenv("TRACELIT_ENDPOINT", "https://ingest.tracelit.app"))
    sample_rate: float = field(default_factory=lambda: float(os.getenv("TRACELIT_SAMPLE_RATE", "1.0")))
    enabled: bool = field(default_factory=lambda: _env_bool("TRACELIT_ENABLED", True))
    resource_attributes: dict[str, Any] = field(default_factory=dict)

    def valid(self) -> list[str]:
        errors: list[str] = []
        if not self.api_key:
            errors.append("TRACELIT_API_KEY is required")
        if not (0.0 <= self.sample_rate <= 1.0):
            errors.append("sample_rate must be between 0.0 and 1.0")
        return errors

    def validate(self) -> None:
        return None

    def resolved_service_name(self) -> str:
        if self.service_name:
            return self.service_name
        for env_name in ("OTEL_SERVICE_NAME", "SERVICE_NAME", "APP_NAME"):
            env_value = os.getenv(env_name)
            if env_value:
                return env_value
        return "unknown-service"

    def detect_framework(self) -> str:
        candidates: dict[str, str] = {
            "django": "django",
            "fastapi": "fastapi",
            "flask": "flask",
            "starlette": "starlette",
            "tornado": "tornado",
            "celery": "celery",
            "aiohttp": "aiohttp",
        }
        for module_name, framework in candidates.items():
            try:
                __import__(module_name)
                return framework
            except Exception:
                continue
        if os.getenv("ASGI_APP"):
            return "asgi"
        if os.getenv("WSGI_APP"):
            return "wsgi"
        return "python"

    def resolved_commit_sha(self) -> str | None:
        env_keys = [
            "COMMIT_SHA",
            "GIT_COMMIT_SHA",
            "GIT_COMMIT",
            "GITHUB_SHA",
            "HEROKU_SLUG_COMMIT",
            "SOURCE_VERSION",
            "RENDER_GIT_COMMIT",
            "FLY_APP_VERSION",
            "RAILWAY_GIT_COMMIT_SHA",
        ]
        for key in env_keys:
            value = os.getenv(key)
            if value:
                return value
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
                timeout=1,
            )
            sha = completed.stdout.strip()
            return sha if sha else None
        except Exception:
            return None

    def sanitized_resource_attributes(self) -> dict[str, str | bool | int | float]:
        safe: dict[str, str | bool | int | float] = {}
        for key, value in self.resource_attributes.items():
            if isinstance(value, (str, bool, int, float)):
                safe[str(key)] = value
        return safe

    def export_headers(self) -> dict[str, str]:
        token = self.api_key or ""
        return {
            "Authorization": f"Bearer {token}",
            "X-Service-Name": self.resolved_service_name(),
            "X-Environment": self.environment,
        }
