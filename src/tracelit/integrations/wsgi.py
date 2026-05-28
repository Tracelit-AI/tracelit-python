from __future__ import annotations

import time

import tracelit


class TracelitWSGIMiddleware:
    def __init__(self, app):
        self.app = app
        self._counter = tracelit.metrics.counter("http.server.request.count", unit="{request}")
        self._duration = tracelit.metrics.histogram("http.server.request.duration", unit="ms")
        self._errors = tracelit.metrics.counter("http.server.error.count", unit="{request}")

    def __call__(self, environ, start_response):
        start = time.perf_counter()
        status_code = 200

        def wrapped_start_response(status, headers, exc_info=None):
            nonlocal status_code
            status_code = int(status.split()[0])
            return start_response(status, headers, exc_info)

        try:
            return self.app(environ, wrapped_start_response)
        finally:
            elapsed = (time.perf_counter() - start) * 1000.0
            attrs = {"http.route": environ.get("PATH_INFO", "/"), "http.method": environ.get("REQUEST_METHOD", "GET")}
            self._counter.add(1, attrs)
            self._duration.record(elapsed, attrs)
            if status_code >= 500:
                self._errors.add(1, attrs)
