# application/validators.py
"""Validateurs pour les DTOs et les données du domaine."""
from datetime import datetime
from typing import Dict, Any
from domain.models.resource import ResourceType


class ResourceValidator:
    """Validateur pour les ressources."""

    @staticmethod
    def validate_create_request(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Valider les données de création d'une ressource.
        
        Returns:
            Dictionnaire des erreurs (clé: champ, valeur: message d'erreur)
        """
        errors = {}

        # Valider le nom
        if not data.get("name") or len(str(data.get("name")).strip()) == 0:
            errors["name"] = "Le nom de la ressource est obligatoire"
        elif len(str(data.get("name"))) > 255:
            errors["name"] = "Le nom ne doit pas dépasser 255 caractères"

        # Valider le type
        if not data.get("type"):
            errors["type"] = "Le type de ressource est obligatoire"
        else:
            try:
                ResourceType(data.get("type"))
            except ValueError:
                errors["type"] = (
                    f"Type invalide. Types acceptés: "
                    f"{', '.join([t.value for t in ResourceType])}"
                )

        # Valider la capacité
        try:
            capacity = int(data.get("capacity", 0))
            if capacity <= 0:
                errors["capacity"] = "La capacité doit être positive"
        except (ValueError, TypeError):
            errors["capacity"] = "La capacité doit être un nombre entier"

        # Valider la localisation
        if not data.get("location") or len(str(data.get("location")).strip()) == 0:
            errors["location"] = "La localisation est obligatoire"

        # Valider le prix
        try:
            price = float(data.get("price", 0))
            if price < 0:
                errors["price"] = "Le prix ne peut pas être négatif"
        except (ValueError, TypeError):
            errors["price"] = "Le prix doit être un nombre"

        return errors


class AvailabilityValidator:
    """Validateur pour la disponibilité."""

    @staticmethod
    def validate_time_range(start_time_str: str, end_time_str: str) -> Dict[str, str]:
        """
        Valider une plage de dates.
        
        Returns:
            Dictionnaire des erreurs
        """
        errors = {}

        try:
            start_time = datetime.fromisoformat(start_time_str)
        except (ValueError, TypeError):
            errors["start_time"] = "Format de date invalide (utiliser ISO format)"
            return errors

        try:
            end_time = datetime.fromisoformat(end_time_str)
        except (ValueError, TypeError):
            errors["end_time"] = "Format de date invalide (utiliser ISO format)"
            return errors

        if end_time <= start_time:
            errors["date_range"] = "La date de fin doit être après la date de début"

        return errors

    @staticmethod
    def validate_quantity(quantity: int) -> Dict[str, str]:
        """Valider la quantité."""
        errors = {}

        try:
            qty = int(quantity)
            if qty <= 0:
                errors["quantity"] = "La quantité doit être positive"
        except (ValueError, TypeError):
            errors["quantity"] = "La quantité doit être un nombre entier"

        return errors

    @staticmethod
    def validate_duration_minutes(duration: int) -> Dict[str, str]:
        """Valider la durée en minutes."""
        errors = {}

        try:
            dur = int(duration)
            if dur <= 0:
                errors["duration_minutes"] = "La durée doit être positive"
        except (ValueError, TypeError):
            errors["duration_minutes"] = "La durée doit être en nombreentier"

        return errors
