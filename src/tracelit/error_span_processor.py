from __future__ import annotations

import queue
import threading
import time
from typing import Any

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import StatusCode


class ErrorSpanProcessor(SpanProcessor):
    QUEUE_CAPACITY = 512
    _SENTINEL = object()

    def __init__(self, exporter: Any) -> None:
        self._exporter = exporter
        self._queue: queue.Queue[Any] = queue.Queue(self.QUEUE_CAPACITY)
        self._shutdown = False
        self._enqueued_span_ids: set[int] = set()
        self._ids_lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="tracelit-error-export")
        self._worker.start()

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        return None

    def _on_ending(self, span: Any) -> None:
        self._maybe_enqueue_error_span(span)

    def on_end(self, span: Any) -> None:
        self._maybe_enqueue_error_span(span)

    def _maybe_enqueue_error_span(self, span: Any) -> None:
        try:
            if span.status.status_code == StatusCode.OK:
                return
            if span.context.trace_flags.sampled:
                return
            span_id = getattr(span.context, "span_id", None)
            if span_id is not None:
                with self._ids_lock:
                    if span_id in self._enqueued_span_ids:
                        return
                    self._enqueued_span_ids.add(span_id)
            self._queue.put_nowait(span)
        except Exception:
            return None

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        try:
            self._queue.put_nowait(self._SENTINEL)
        except Exception:
            pass
        self._worker.join(timeout=1.0)

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        deadline = time.time() + (timeout_millis / 1000.0)
        while not self._queue.empty() and time.time() < deadline:
            time.sleep(0.01)
        return True

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is self._SENTINEL:
                break
            try:
                self._exporter.export([item])
            except Exception:
                continue
