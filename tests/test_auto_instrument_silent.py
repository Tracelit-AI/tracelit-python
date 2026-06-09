from __future__ import annotations

import logging

from tracelit.auto_instrument import _activate_instrumentation, instrument_all


def test_instrument_all_skips_missing_packages_without_warnings(caplog):
    caplog.set_level(logging.WARNING, logger="tracelit-test")
    logger = logging.getLogger("tracelit-test")

    with caplog.at_level(logging.WARNING, logger="tracelit-test"):
        instrument_all(logger)

    assert not [r for r in caplog.records if "failed to instrument" in r.message]


def test_activate_instrumentation_skips_missing_package_silently():
    logger = logging.getLogger("tracelit-test-skip")
    _activate_instrumentation("opentelemetry-instrumentation-definitely-missing", logger, set())
