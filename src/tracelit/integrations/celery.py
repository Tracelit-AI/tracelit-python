from __future__ import annotations


def install_celery_hook() -> None:
    try:
        from celery import signals
    except Exception:
        return

    @signals.worker_process_init.connect  # type: ignore[misc]
    def _on_worker_start(*args, **kwargs) -> None:
        import tracelit

        tracelit.auto_start()
