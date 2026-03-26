# logger.py
"""Configuration du logging pour le Inventory Service."""
import logging
import logging.handlers
from typing import Optional
from config import Config, LogConfig


def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """
    Configurer le logging pour l'application.
    
    Args:
        config: Configuration du logging (utilise Config par défaut)
        
    Returns:
        Logger configuré
    """
    if config is None:
        config = Config.get_log_config()

    # Créer le logger
    logger = logging.getLogger("inventory_service")
    logger.setLevel(config.level)

    # Format du logging
    formatter = logging.Formatter(config.format)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler fichier (optionnel)
    if config.file:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=config.file,
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Impossible de configurer le logging fichier: {e}")

    return logger


# Logger global
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Obtenir un logger pour un module spécifique.
    
    Args:
        name: Nom du module ou logger
        
    Returns:
        Logger configuré
    """
    return logging.getLogger(f"inventory_service.{name}")
