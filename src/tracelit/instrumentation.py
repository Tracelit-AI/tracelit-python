from __future__ import annotations

import atexit
import logging
import threading

from opentelemetry import _logs, metrics as otel_metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import set_tracer_provider

from tracelit.auto_instrument import instrument_all
from tracelit.configuration import Configuration
from tracelit.error_always_on_sampler import ErrorAlwaysOnSampler
from tracelit.error_span_processor import ErrorSpanProcessor
from tracelit.logger_bridge import install_logging_bridge
from tracelit.metrics import restart_pollers, setup as setup_metrics
from tracelit.version import VERSION

_configured = False
_lock = threading.Lock()
_logger = logging.getLogger("tracelit")


def start(config: Configuration) -> None:
    global _configured
    with _lock:
        if _configured or not config.enabled:
            return

        errors = config.valid()
        if errors:
            _logger.warning("[Tracelit] disabled — %s", ", ".join(errors))
            return

        resource_attrs = {
            SERVICE_NAME: config.resolved_service_name(),
            "deployment.environment": config.environment,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": config.detect_framework(),
            "telemetry.sdk.version": VERSION,
            **config.sanitized_resource_attributes(),
        }
        sha = config.resolved_commit_sha()
        if sha:
            resource_attrs["service.commit_sha"] = sha

        try:
            resource = Resource.create(resource_attrs)
        except Exception as exc:
            _logger.warning("[Tracelit] could not set resource attributes: %s", exc)
            resource = Resource.create({})

        trace_exporter = OTLPSpanExporter(endpoint=f"{config.endpoint}/v1/traces", headers=config.export_headers())
        if config.sample_rate < 1.0:
            sampler = ParentBased(root=ErrorAlwaysOnSampler(TraceIdRatioBased(config.sample_rate)))
            provider = TracerProvider(resource=resource, sampler=sampler)
        else:
            provider = TracerProvider(resource=resource)

        provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        provider.add_span_processor(ErrorSpanProcessor(trace_exporter))
        set_tracer_provider(provider)

        _setup_logs(config, resource)
        _setup_metrics(config, resource)

        instrument_all(_logger)
        _configure_fork_safety()

        _configured = True
        atexit.register(shutdown)


def _setup_logs(config: Configuration, resource: Resource) -> None:
    try:
        log_exporter = OTLPLogExporter(endpoint=f"{config.endpoint}/v1/logs", headers=config.export_headers())
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        _logs.set_logger_provider(logger_provider)
        install_logging_bridge(logger_provider)
        root = logging.getLogger()
        if not any(isinstance(h, LoggingHandler) for h in root.handlers):
            root.addHandler(LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider))
    except Exception as exc:
        _logger.warning("[Tracelit] failed to set up logs: %s", exc)


def _setup_metrics(config: Configuration, resource: Resource) -> None:
    try:
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{config.endpoint}/v1/metrics",
            headers=config.export_headers(),
        )
        reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=60000,
            export_timeout_millis=10000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        from opentelemetry import metrics as otel_metrics

        otel_metrics.set_meter_provider(meter_provider)
        setup_metrics(config.resolved_service_name(), VERSION)
    except Exception as exc:
        _logger.warning("[Tracelit] failed to set up metrics: %s", exc)


def _configure_fork_safety() -> None:
    try:
        import os

        os.register_at_fork(after_in_child=restart_pollers)
    except Exception:
        return


def shutdown() -> None:
    try:
        trace.get_tracer_provider().shutdown()
    except Exception:
        pass
    try:
        _logs.get_logger_provider().shutdown()
    except Exception:
        pass
    try:
        meter_provider = otel_metrics.get_meter_provider()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()
    except Exception:
        pass


def reset() -> None:
    global _configured
    _configured = False
