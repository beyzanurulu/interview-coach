import logging

import structlog


def configure_logging(level: str = "INFO", json: bool = False) -> None:
    """structlog yapılandırması. Loglara transkript metni yazılmaz; sadece ID ve metrikler."""
    logging.basicConfig(format="%(message)s", level=level)
    renderer = structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
    )
