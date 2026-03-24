"""
Schémas Pydantic — Validation des données entrantes/sortantes (DTO)

📚 Explication Pédagogique :
Les schémas Pydantic sont des Data Transfer Objects (DTO).
Ils valident et sérialisent les données entre l'API et le domaine.

Flux :
  Client HTTP → JSON → Schema Pydantic (validation) → Domaine → Repository → DB
  DB → Repository → Domaine → Schema Pydantic (sérialisation) → JSON → Client HTTP

C'est un contrat d'API clair : chaque service sait exactement
quel format de données envoyer au log-service.

🔑 C'est aussi le "contrat de communication entre services" (CDC exercice 5)
Les autres services (auth, booking, payment, inventory) doivent
respecter ces schémas pour envoyer des logs.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ────────────────── System Log Schemas ──────────────────

class SystemLogCreateRequest(BaseModel):
    """
    Schéma pour CRÉER un log système.
    
    C'est ce que les autres services envoient au log-service.
    Exemple d'appel depuis auth-service :
    
    POST /api/v1/system-logs
    {
        "service_name": "auth-service",
        "level": "INFO",
        "message": "User logged in successfully",
        "correlation_id": "abc-123",
        "metadata": {"user_id": "456", "ip": "192.168.1.1"}
    }
    """
    service_name: str = Field(..., min_length=1, max_length=100, description="Nom du service émetteur")
    level: str = Field(..., description="Niveau : DEBUG, INFO, WARNING, ERROR, CRITICAL")
    message: str = Field(..., min_length=1, description="Message du log")
    correlation_id: Optional[str] = Field(None, max_length=36, description="ID de traçabilité inter-services")
    metadata: Optional[dict] = Field(default_factory=dict, description="Données additionnelles")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "auth-service",
                "level": "INFO",
                "message": "User login successful",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {"user_id": "123", "ip_address": "192.168.1.1"}
            }
        }


class SystemLogResponse(BaseModel):
    """Schéma de réponse pour un log système."""
    id: str
    service_name: str
    level: str
    message: str
    correlation_id: Optional[str] = None
    timestamp: datetime
    metadata: dict = {}


class SystemLogListResponse(BaseModel):
    """Réponse paginée pour la liste des logs système."""
    items: list[SystemLogResponse]
    total: int
    limit: int
    offset: int


# ────────────────── Audit Log Schemas ──────────────────

class AuditLogCreateRequest(BaseModel):
    """
    Schéma pour CRÉER un log d'audit.
    
    Exemple d'appel depuis booking-service :
    
    POST /api/v1/audit-logs
    {
        "user_id": "user-456",
        "action": "CREATE",
        "entity": "Booking",
        "entity_id": "booking-789",
        "correlation_id": "abc-123",
        "details": {"room": "Suite 101", "dates": "2026-04-01 → 2026-04-05"}
    }
    """
    user_id: str = Field(..., min_length=1, description="ID de l'utilisateur")
    action: str = Field(..., min_length=1, max_length=50, description="Type d'action")
    entity: str = Field(..., min_length=1, max_length=100, description="Entité affectée")
    entity_id: str = Field(..., min_length=1, description="ID de l'entité")
    correlation_id: Optional[str] = Field(None, max_length=36)
    details: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-456",
                "action": "CREATE",
                "entity": "Booking",
                "entity_id": "booking-789",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "details": {"resource": "Suite 101"}
            }
        }


class AuditLogResponse(BaseModel):
    """Schéma de réponse pour un log d'audit."""
    id: str
    user_id: str
    action: str
    entity: str
    entity_id: str
    correlation_id: Optional[str] = None
    timestamp: datetime
    details: dict = {}


class AuditLogListResponse(BaseModel):
    """Réponse paginée pour la liste des logs d'audit."""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


# ────────────────── Health Check ──────────────────

class HealthResponse(BaseModel):
    """Réponse du health check."""
    status: str = "healthy"
    service: str = "log-service"
    version: str = "1.0.0"
    database: str = "connected"
