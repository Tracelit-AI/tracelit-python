from __future__ import annotations

import os
import threading
import time
from typing import Any

from opentelemetry import metrics

os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE", "delta")


_meter = None
_pollers_started = False


class MetricsFacade:
    def counter(self, name: str, description: str = "", unit: str = "") -> Any:
        return _meter.create_counter(name, description=description, unit=unit) if _meter else _NoopMetric()

    def histogram(self, name: str, description: str = "", unit: str = "") -> Any:
        return _meter.create_histogram(name, description=description, unit=unit) if _meter else _NoopMetric()

    def gauge(self, name: str, description: str = "", unit: str = "") -> Any:
        if _meter and hasattr(_meter, "create_gauge"):
            return _meter.create_gauge(name, description=description, unit=unit)
        return _NoopMetric()


class _NoopMetric:
    def add(self, *args, **kwargs) -> None:
        return None

    def record(self, *args, **kwargs) -> None:
        return None


def setup(service_name: str, version: str) -> None:
    global _meter
    _meter = metrics.get_meter(service_name, version=version)
    _start_pollers()


def restart_pollers() -> None:
    global _pollers_started
    _pollers_started = False
    _start_pollers()


def _start_pollers() -> None:
    global _pollers_started
    if _pollers_started or not _meter:
        return
    _pollers_started = True
    _start_memory_poller()
    _start_cpu_poller()


def _start_memory_poller() -> None:
    gauge = MetricsFacade().gauge("process.memory.rss", description="Resident memory", unit="By")

    def loop() -> None:
        while True:
            try:
                import resource

                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                gauge.record(float(rss))
            except Exception:
                pass
            time.sleep(60)

    threading.Thread(target=loop, daemon=True, name="tracelit-memory-poller").start()


def _start_cpu_poller() -> None:
    gauge = MetricsFacade().gauge("process.runtime.cpu.usage", description="CPU usage", unit="%")

    def loop() -> None:
        while True:
            try:
                with open("/proc/stat", "r", encoding="utf-8") as f:
                    first = f.readline().split()[1:5]
                total = sum(int(v) for v in first)
                idle = int(first[3])
                usage = (0.0 if total == 0 else (1.0 - idle / total) * 100.0)
                gauge.record(usage)
            except Exception:
                pass
            time.sleep(30)

    threading.Thread(target=loop, daemon=True, name="tracelit-cpu-poller").start()
