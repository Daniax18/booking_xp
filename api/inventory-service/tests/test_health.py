"""
tests/test_health.py
Tests pour l'endpoint de santé
"""
import pytest


class TestHealth:
    """Tests pour le health check."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test le health check."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"
