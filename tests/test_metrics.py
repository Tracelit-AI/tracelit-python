from tracelit.metrics import MetricsFacade


def test_metrics_facade_noop():
    counter = MetricsFacade().counter("test")
    counter.add(1)
