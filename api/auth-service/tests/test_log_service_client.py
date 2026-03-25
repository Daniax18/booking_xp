import httpx
import pytest

from adapters.outbound.log_service_client import HttpLogServiceClient


class DummyResponse:
    """Provide a minimal response object with success semantics."""

    def raise_for_status(self):
        """Do nothing because this fake response is always successful."""
        return None


@pytest.mark.asyncio
async def test_create_audit_log_calls_expected_endpoint(monkeypatch):
    """Ensure audit logs are posted to the audit endpoint."""
    calls = []

    async def fake_post(self, url, json):
        """Capture outgoing HTTP request data for assertions."""
        calls.append((url, json))
        return DummyResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = HttpLogServiceClient(base_url="http://log-service:8005", service_name="auth-service")
    await client.create_audit_log(
        user_id="u-1",
        action="LOGIN",
        entity="user",
        entity_id="u-1",
        details={"source": "test"},
    )

    assert len(calls) == 1
    assert calls[0][0].endswith("/api/v1/audit-logs")
    assert calls[0][1]["action"] == "LOGIN"


@pytest.mark.asyncio
async def test_create_system_log_calls_expected_endpoint(monkeypatch):
    """Ensure system logs are posted to the system endpoint."""
    calls = []

    async def fake_post(self, url, json):
        """Capture outgoing HTTP request data for assertions."""
        calls.append((url, json))
        return DummyResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = HttpLogServiceClient(base_url="http://log-service:8005", service_name="auth-service")
    await client.create_system_log(level="INFO", message="hello", metadata={"k": "v"})

    assert len(calls) == 1
    assert calls[0][0].endswith("/api/v1/system-logs")
    assert calls[0][1]["service_name"] == "auth-service"
