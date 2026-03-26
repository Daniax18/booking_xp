import logging

import structlog

from infrastructure.config import get_settings
from infrastructure.middleware import get_correlation_id


def add_correlation_id(logger, method_name, event_dict):
    """Inject the current correlation identifier into every structured log."""
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    return event_dict


def add_service_name(logger, method_name, event_dict):
    """Inject the service name into every structured log."""
    event_dict['service'] = get_settings().SERVICE_NAME
    return event_dict


def setup_logging() -> None:
    """Configure structlog and standard logging for JSON-style observability."""
    settings = get_settings()
    shared_processors = [
        structlog.stdlib.add_log_level,
        add_service_name,
        add_correlation_id,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = structlog.processors.JSONRenderer() if settings.LOG_FORMAT == 'json' else structlog.dev.ConsoleRenderer(colors=True)
    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(processor=renderer, foreign_pre_chain=shared_processors)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG if settings.DATABASE_ECHO else logging.WARNING)
