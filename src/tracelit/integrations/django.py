from __future__ import annotations

from django.apps import AppConfig


class TracelitConfig(AppConfig):
    name = "tracelit.integrations.django"
    verbose_name = "Tracelit"

    def ready(self) -> None:
        import tracelit

        tracelit.auto_start()
