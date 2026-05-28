from opentelemetry.trace import Status, StatusCode

from tracelit.error_span_processor import ErrorSpanProcessor


class DummyExporter:
    def __init__(self):
        self.exported = []

    def export(self, spans):
        self.exported.extend(spans)


class DummyFlags:
    def __init__(self, sampled):
        self.sampled = sampled


class DummyContext:
    def __init__(self, sampled, span_id=1):
        self.trace_flags = DummyFlags(sampled)
        self.span_id = span_id


class DummySpan:
    def __init__(self, status, sampled=False, span_id=1):
        self.status = Status(status)
        self.context = DummyContext(sampled, span_id=span_id)


def test_processor_exports_unsampled_error():
    exporter = DummyExporter()
    processor = ErrorSpanProcessor(exporter)
    processor.on_end(DummySpan(StatusCode.ERROR, sampled=False))
    processor.force_flush(1000)
    processor.shutdown()
    assert len(exporter.exported) == 1


def test_processor_supports_on_ending_hook_without_duplicate_export():
    exporter = DummyExporter()
    processor = ErrorSpanProcessor(exporter)
    span = DummySpan(StatusCode.ERROR, sampled=False, span_id=42)
    processor._on_ending(span)
    processor.on_end(span)
    processor.force_flush(1000)
    processor.shutdown()
    assert len(exporter.exported) == 1
