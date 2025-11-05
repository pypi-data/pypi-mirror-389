"""Structured logging configuration."""

import logging
import sys
from typing import Any, Optional

import structlog


def configure_logging(
    log_level: str = "INFO", log_file: Optional[str] = None
) -> structlog.BoundLogger:
    """Configure structured logging with rich console output."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    return structlog.get_logger()  # type: ignore[no-any-return]


def get_logger(name: Optional[str] = None, **kwargs: Any) -> structlog.BoundLogger:
    """Get a logger instance with optional context."""
    logger = structlog.get_logger(name)
    if kwargs:
        logger = logger.bind(**kwargs)
    return logger  # type: ignore[no-any-return]
