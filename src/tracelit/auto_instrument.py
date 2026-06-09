from __future__ import annotations

import importlib
import inspect
import os
from typing import Any

_instrumented: set[str] = set()


def _disabled_names() -> set[str]:
    raw = os.getenv("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", "")
    return {x.strip() for x in raw.split(",") if x.strip()}


def instrument_all(logger: Any) -> None:
    disabled = _disabled_names()
    try:
        from opentelemetry.instrumentation.bootstrap_gen import default_instrumentations, libraries
    except Exception as exc:
        logger.warning("[Tracelit] failed to load bootstrap registry: %s", exc)
        return

    for requirement in default_instrumentations:
        package = requirement.split("==")[0]
        if not _instrumentation_package_installed(package):
            continue
        _activate_instrumentation(package, logger, disabled)

    for item in libraries:
        requirement = item.get("instrumentation", "")
        package = requirement.split("==")[0]
        library = item.get("library", "").split()[0]
        if not library:
            continue
        if importlib.util.find_spec(library) is None:
            continue
        if not _instrumentation_package_installed(package):
            continue
        _activate_instrumentation(package, logger, disabled)


def _instrumentation_package_installed(package: str) -> bool:
    return importlib.util.find_spec(package.replace("-", ".")) is not None


def _activate_instrumentation(package: str, logger: Any, disabled: set[str]) -> None:
    short = package.removeprefix("opentelemetry-instrumentation-")
    if short in disabled or package in _instrumented:
        return
    if _should_skip_instrumentation(short):
        return
    try:
        module = importlib.import_module(package.replace("-", "."))
        instrumentor = getattr(module, "instrumentor", None)
        if instrumentor and hasattr(instrumentor, "instrument"):
            instrumentor.instrument()
        else:
            # Standard entry point used by most contrib instrumentations.
            _instrument_first_concrete_class(module)
        _instrumented.add(package)
    except Exception as exc:
        if _is_benign_instrumentation_failure(exc):
            return
        logger.warning("[Tracelit] failed to instrument %s: %s", package, exc)


def _should_skip_instrumentation(short_name: str) -> bool:
    if short_name == "django" and not os.environ.get("DJANGO_SETTINGS_MODULE"):
        return True
    return False


def _is_benign_instrumentation_failure(exc: Exception) -> bool:
    if isinstance(exc, ModuleNotFoundError):
        return True
    message = str(exc)
    if isinstance(exc, ImportError) and (
        "opentelemetry.instrumentation" in message or "No module named" in message
    ):
        return True
    if "settings are not configured" in message:
        return True
    return False


def _instrument_first_concrete_class(module: Any) -> None:
    classes = []
    for value in module.__dict__.values():
        if not inspect.isclass(value):
            continue
        if not value.__name__.endswith("Instrumentor"):
            continue
        if value.__name__ == "BaseInstrumentor":
            continue
        if value.__module__ != module.__name__:
            continue
        if inspect.isabstract(value):
            continue
        classes.append(value)
    for cls in classes:
        instance = cls()
        if hasattr(instance, "instrument"):
            instance.instrument()
            return
