"""Validateurs pour les DTOs et les donnees du domaine."""
from datetime import datetime
from typing import Any, Dict

from domain.models.resource import ResourceType


class ResourceValidator:
    """Valider les donnees de creation et mise a jour d'une ressource."""

    @staticmethod
    def validate_create_request(data: Dict[str, Any]) -> Dict[str, str]:
        errors = {}
        if not data.get('name') or len(str(data.get('name')).strip()) == 0:
            errors['name'] = 'Le nom de la ressource est obligatoire'
        elif len(str(data.get('name'))) > 255:
            errors['name'] = 'Le nom ne doit pas depasser 255 caracteres'

        if not data.get('type'):
            errors['type'] = 'Le type de ressource est obligatoire'
        else:
            try:
                ResourceType(data.get('type'))
            except ValueError:
                errors['type'] = f"Type invalide. Types acceptes: {', '.join([t.value for t in ResourceType])}"

        try:
            capacity = int(data.get('capacity', 0))
            if capacity <= 0:
                errors['capacity'] = 'La capacite doit etre positive'
        except (ValueError, TypeError):
            errors['capacity'] = 'La capacite doit etre un nombre entier'

        if not data.get('location') or len(str(data.get('location')).strip()) == 0:
            errors['location'] = 'La localisation est obligatoire'

        try:
            price = float(data.get('price', 0))
            if price < 0:
                errors['price'] = 'Le prix ne peut pas etre negatif'
        except (ValueError, TypeError):
            errors['price'] = 'Le prix doit etre un nombre'
        return errors


class AvailabilityValidator:
    """Valider les donnees de disponibilite avant passage au domaine."""

    @staticmethod
    def validate_time_range(start_time_str: str, end_time_str: str) -> Dict[str, str]:
        errors = {}
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except (ValueError, TypeError):
            errors['start_time'] = 'Format de date invalide (utiliser ISO format)'
            return errors

        try:
            end_time = datetime.fromisoformat(end_time_str)
        except (ValueError, TypeError):
            errors['end_time'] = 'Format de date invalide (utiliser ISO format)'
            return errors

        if end_time <= start_time:
            errors['date_range'] = 'La date de fin doit etre apres la date de debut'
        return errors

    @staticmethod
    def validate_quantity(quantity: int) -> Dict[str, str]:
        """Allow zero when a slot is fully consumed by bookings."""
        errors = {}
        try:
            qty = int(quantity)
            if qty < 0:
                errors['quantity'] = 'La quantite ne peut pas etre negative'
        except (ValueError, TypeError):
            errors['quantity'] = 'La quantite doit etre un nombre entier'
        return errors

    @staticmethod
    def validate_duration_minutes(duration: int) -> Dict[str, str]:
        errors = {}
        try:
            dur = int(duration)
            if dur <= 0:
                errors['duration_minutes'] = 'La duree doit etre positive'
        except (ValueError, TypeError):
            errors['duration_minutes'] = 'La duree doit etre en nombre entier'
        return errors
