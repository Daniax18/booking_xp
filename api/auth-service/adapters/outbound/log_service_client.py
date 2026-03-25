from typing import Optional

import httpx

from domain.ports.outbound import AuditLogPort, SystemLogPort


class HttpLogServiceClient(AuditLogPort, SystemLogPort):
    """Call log-service HTTP endpoints to publish audit and system logs."""

    def __init__(self, base_url: str, service_name: str, timeout_seconds: float = 5.0):
        """Store destination URL, service identity, and request timeout."""
        self._base_url = base_url.rstrip("/")
        self._service_name = service_name
        self._timeout_seconds = timeout_seconds

    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Send an audit action to log-service."""
        payload = {
            "user_id": user_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "correlation_id": correlation_id,
            "details": details or {},
        }

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(f"{self._base_url}/api/v1/audit-logs", json=payload)
            response.raise_for_status()

    async def create_system_log(
        self,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Send a technical service log to log-service."""
        payload = {
            "service_name": self._service_name,
            "level": level,
            "message": message,
            "correlation_id": correlation_id,
            "metadata": metadata or {},
        }

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(f"{self._base_url}/api/v1/system-logs", json=payload)
            response.raise_for_status()
