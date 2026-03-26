"""
HTTP Audit Service Client — Adaptateur pour log-service (audit logs)

📚 Explication Pédagogique :
Cet adaptateur envoie les logs d'audit au log-service pour conformité.
"""
from typing import Optional
import httpx
from domain.ports.outbound import AuditLogPort


class HttpAuditServiceClient(AuditLogPort):
    """Client HTTP pour envoyer des logs d'audit au log-service."""
    
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
    
    async def log_action(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details: Optional[dict] = None,
    ) -> None:
        """Envoyer un log d'audit."""
        payload = {
            "user_id": user_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "details": details or {},
        }
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                await client.post(
                    f"{self._base_url}/api/v1/audit-logs",
                    json=payload,
                )
        except Exception:
            # L'audit ne doit pas bloquer le service
            pass
