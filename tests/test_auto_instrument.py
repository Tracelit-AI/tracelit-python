from __future__ import annotations

import types
from abc import ABC, abstractmethod

from tracelit.auto_instrument import _instrument_first_concrete_class


class BaseInstrumentor(ABC):
    @abstractmethod
    def instrument(self):
        raise NotImplementedError


class ConcreteInstrumentor:
    called = False

    def instrument(self):
        type(self).called = True


def test_skips_abstract_base_and_instruments_concrete_class():
    ConcreteInstrumentor.called = False
    BaseInstrumentor.__module__ = "fake.module"
    ConcreteInstrumentor.__module__ = "fake.module"

    module = types.SimpleNamespace(
        __name__="fake.module",
        BaseInstrumentor=BaseInstrumentor,
        ConcreteInstrumentor=ConcreteInstrumentor,
    )

    _instrument_first_concrete_class(module)

    assert ConcreteInstrumentor.called is True
