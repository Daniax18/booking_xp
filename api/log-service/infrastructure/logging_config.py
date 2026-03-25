"""
Logging Configuration — Logs structurés avec structlog

📚 Explication Pédagogique :
Les logs structurés (JSON) sont essentiels en production.

Log classique (mauvais pour le parsing) :
    2026-03-25 10:30:15 - ERROR - User 123 failed to book room 456

Log structuré (facilement parsable par ELK, Datadog, etc.) :
    {"timestamp": "2026-03-25T10:30:15Z", "level": "ERROR",
     "service": "booking-service", "user_id": "123",
     "resource_id": "456", "action": "book_room",
     "correlation_id": "abc-123", "message": "Booking failed"}

Avantages :
→ Recherche facile : "donne-moi tous les errors du booking-service"
→ Filtrage par correlation_id, user_id, etc.
→ Agrégation et dashboards automatiques
→ Compatibilité avec les outils de monitoring (ELK, Grafana, Datadog)
"""
import logging
import structlog
from infrastructure.config import get_settings
from infrastructure.middleware import get_correlation_id


def add_correlation_id(logger, method_name, event_dict):
    """Processeur structlog : ajouter automatiquement le correlation_id."""
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_service_name(logger, method_name, event_dict):
    """Processeur structlog : ajouter le nom du service."""
    settings = get_settings()
    event_dict["service"] = settings.SERVICE_NAME
    return event_dict


def setup_logging():
    """
    Configurer structlog pour des logs JSON structurés.
    
    La chaîne de processeurs :
    1. add_log_level → ajoute "level": "INFO"
    2. add_service_name → ajoute "service": "log-service"
    3. add_correlation_id → ajoute "correlation_id": "abc-123"
    4. TimeStamper → ajoute "timestamp": "2026-03-25T..."
    5. JSONRenderer → formatte tout en JSON
    """
    settings = get_settings()

    # Processeurs communs
    shared_processors = [
        structlog.stdlib.add_log_level,
        add_service_name,
        add_correlation_id,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configurer aussi le logging standard Python
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Réduire le bruit des logs de librairies
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DATABASE_ECHO else logging.WARNING
    )
