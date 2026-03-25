"""
tests/test_health.py
Tests pour l'endpoint de santé
"""


class TestHealth:
    """Tests pour le health check."""
    
    def test_health_check(self, test_client):
        """Test le health check."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"
