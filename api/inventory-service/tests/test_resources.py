"""
tests/test_resources.py
Tests pour les endpoints de ressources
"""
import pytest
from datetime import datetime


class TestCreateResource:
    """Tests pour la création de ressources."""
    
    def test_create_resource_success(self, test_client, sample_resource_data):
        """Test la création réussie d'une ressource."""
        response = test_client.post("/resources", json=sample_resource_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_resource_data["name"]
        assert data["type"] == sample_resource_data["type"]
        assert data["capacity"] == sample_resource_data["capacity"]
        assert "id" in data
        assert data["is_active"] == True
    
    def test_create_resource_missing_name(self, test_client):
        """Test la création avec nom manquant."""
        data = {
            "type": "room",
            "description": "Test",
            "capacity": 10,
            "location": "Test",
            "price": 50.0
        }
        response = test_client.post("/resources", json=data)
        assert response.status_code in [400, 422]  # Validation error
    
    def test_create_resource_invalid_capacity(self, test_client):
        """Test la création avec capacité invalide."""
        data = {
            "name": "Test",
            "type": "room",
            "description": "Test",
            "capacity": -1,  # ❌ Invalide
            "location": "Test",
            "price": 50.0
        }
        response = test_client.post("/resources", json=data)
        # S'il y a validation au niveau DTO
        assert response.status_code in [400, 422]
    
    def test_create_resource_invalid_type(self, test_client):
        """Test avec type invalide."""
        data = {
            "name": "Test",
            "type": "invalid_type",  # ❌ Invalide
            "description": "Test",
            "capacity": 10,
            "location": "Test",
            "price": 50.0
        }
        response = test_client.post("/resources", json=data)
        assert response.status_code in [400, 422]


class TestGetResource:
    """Tests pour la récupération de ressources."""
    
    def test_get_resource_success(self, test_client, sample_resource_data):
        """Test la récupération d'une ressource."""
        # Créer d'abord
        create_response = test_client.post("/resources", json=sample_resource_data)
        resource_id = create_response.json()["id"]
        
        # Récupérer
        get_response = test_client.get(f"/resources/{resource_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == resource_id
        assert data["name"] == sample_resource_data["name"]
    
    def test_get_resource_not_found(self, test_client):
        """Test la récupération d'une ressource inexistante."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = test_client.get(f"/resources/{fake_id}")
        assert response.status_code == 404


class TestListResources:
    """Tests pour la liste des ressources."""
    
    def test_list_resources_empty(self, test_client):
        """Test la liste vide."""
        response = test_client.get("/resources")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_resources_with_items(self, test_client, sample_resource_data):
        """Test la liste avec ressources."""
        # Créer 2 ressources
        test_client.post("/resources", json=sample_resource_data)
        test_client.post("/resources", json=sample_resource_data)
        
        # Lister
        response = test_client.get("/resources")
        assert response.status_code == 200
        assert len(response.json()) >= 2
    
    def test_list_resources_by_type(self, test_client, sample_resource_data):
        """Test la liste filtrée par type."""
        test_client.post("/resources", json=sample_resource_data)
        
        response = test_client.get("/resources?type=room")
        assert response.status_code == 200
        resources = response.json()
        assert all(r["type"] == "room" for r in resources)


class TestUpdateResource:
    """Tests pour la mise à jour de ressources."""
    
    def test_update_resource_success(self, test_client, sample_resource_data):
        """Test la mise à jour réussie."""
        # Créer
        create_response = test_client.post("/resources", json=sample_resource_data)
        resource_id = create_response.json()["id"]
        
        # Mettre à jour
        update_data = {"name": "Nouveau Nom", "price": 200.0}
        update_response = test_client.put(
            f"/resources/{resource_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Nouveau Nom"
        assert data["price"] == 200.0


class TestDeactivateResource:
    """Tests pour la désactivation."""
    
    def test_deactivate_resource(self, test_client, sample_resource_data):
        """Test la désactivation d'une ressource."""
        # Créer
        create_response = test_client.post("/resources", json=sample_resource_data)
        resource_id = create_response.json()["id"]
        
        # Désactiver
        response = test_client.post(f"/resources/{resource_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] == False


class TestActivateResource:
    """Tests pour l'activation."""
    
    def test_activate_resource(self, test_client, sample_resource_data):
        """Test l'activation d'une ressource."""
        # Créer et désactiver
        create_response = test_client.post("/resources", json=sample_resource_data)
        resource_id = create_response.json()["id"]
        test_client.post(f"/resources/{resource_id}/deactivate")
        
        # Activer
        response = test_client.post(f"/resources/{resource_id}/activate")
        assert response.status_code == 200
        assert response.json()["is_active"] == True
