"""
HTTP Log Service Client — Adaptateur pour log-service

📚 Explication Pédagogique :
Cet adaptateur communique avec le log-service pour centraliser les logs.
C'est une communication inter-services (microservices pattern).
"""
from typing import Optional
import httpx
from domain.ports.outbound import SystemLogPort


class HttpLogServiceClient(SystemLogPort):
    """Client HTTP pour envoyer des logs au log-service."""
    
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
    
    async def log(
        self,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Envoyer un log système au log-service."""
        payload = {
            "service_name": "payment-service",
            "level": level,
            "message": message,
            "metadata": metadata or {},
        }
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                await client.post(
                    f"{self._base_url}/api/v1/system-logs",
                    json=payload,
                )
        except Exception:
            # Le paiement ne doit pas échouer si le log-service est down
            pass
