from __future__ import annotations

import time

import tracelit


class TracelitASGIMiddleware:
    def __init__(self, app):
        self.app = app
        self._counter = tracelit.metrics.counter("http.server.request.count", unit="{request}")
        self._duration = tracelit.metrics.histogram("http.server.request.duration", unit="ms")
        self._errors = tracelit.metrics.counter("http.server.error.count", unit="{request}")

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        start = time.perf_counter()
        status_code = 200

        async def wrapped_send(message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message.get("status", 200))
            await send(message)

        try:
            return await self.app(scope, receive, wrapped_send)
        finally:
            elapsed = (time.perf_counter() - start) * 1000.0
            attrs = {"http.route": scope.get("path", "/"), "http.method": scope.get("method", "GET")}
            self._counter.add(1, attrs)
            self._duration.record(elapsed, attrs)
            if status_code >= 500:
                self._errors.add(1, attrs)
