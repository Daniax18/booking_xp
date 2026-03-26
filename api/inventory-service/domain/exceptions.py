# domain/exceptions.py
"""Exceptions du domaine de l'Inventory Service."""


class DomainException(Exception):
    """Classe de base pour les exceptions du domaine."""
    pass


class ResourceNotFound(DomainException):
    """La ressource n'existe pas."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Ressource avec l'ID {resource_id} non trouvée")


class ResourceAlreadyExists(DomainException):
    """La ressource existe déjà."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Ressource avec l'ID {resource_id} existe déjà")


class ResourceInactive(DomainException):
    """La ressource est inactive."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"La ressource {resource_id} est inactive")


class NoAvailabilityFound(DomainException):
    """Aucune disponibilité trouvée pour la ressource."""
    def __init__(self, resource_id: str, start_time: str, end_time: str):
        super().__init__(
            f"Aucune disponibilité pour la ressource {resource_id} "
            f"entre {start_time} et {end_time}"
        )


class InsufficientCapacity(DomainException):
    """Capacité insuffisante pour la ressource."""
    def __init__(self, resource_id: str, requested: int, available: int):
        super().__init__(
            f"Capacité insuffisante pour {resource_id}. "
            f"Demandé: {requested}, Disponible: {available}"
        )


class AvailabilityOverlapError(DomainException):
    """Les créneaux de disponibilité se chevauchent."""
    def __init__(self, slot_id_1: str, slot_id_2: str):
        super().__init__(
            f"Les créneaux {slot_id_1} et {slot_id_2} se chevauchent"
        )


class InvalidDateRange(DomainException):
    """La plage de dates est invalide."""
    def __init__(self, start_time: str, end_time: str):
        super().__init__(
            f"Plage de dates invalide: {start_time} -> {end_time}"
        )
