"""
tests/test_availability.py
Tests pour les endpoints de disponibilité
"""
import pytest
from datetime import datetime, timedelta


class TestCreateAvailabilitySlot:
    """Tests pour la création de créneaux."""
    
    @pytest.mark.asyncio
    async def test_create_availability_success(
        self, async_client, sample_resource_data, sample_availability_data
    ):
        """Test la création réussie d'un créneau."""
        # Créer une ressource d'abord
        resource_response = await async_client.post("/resources", json=sample_resource_data)
        resource_id = resource_response.json()["id"]
        
        # Créer un créneau
        sample_availability_data["resource_id"] = resource_id
        response = await async_client.post(
            f"/resources/{resource_id}/availability",
            json=sample_availability_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["resource_id"] == resource_id
        assert "id" in data
        assert data["is_available"] == True
    
    @pytest.mark.asyncio
    async def test_create_availability_invalid_date_range(
        self, async_client, sample_resource_data
    ):
        """Test avec plage de dates invalide."""
        # Créer une ressource
        resource_response = await async_client.post("/resources", json=sample_resource_data)
        resource_id = resource_response.json()["id"]
        
        # Créer un créneau avec fin avant début
        start = datetime.now()
        end = start - timedelta(hours=1)  # ❌ Invalide
        
        response = await async_client.post(
            f"/resources/{resource_id}/availability",
            json={
                "resource_id": resource_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "quantity": 1
            }
        )
        
        assert response.status_code in [400, 422]


class TestCheckAvailability:
    """Tests pour la vérification de disponibilité."""
    
    @pytest.mark.asyncio
    async def test_check_availability_available(
        self, async_client, sample_resource_data, sample_availability_data
    ):
        """Test la vérification quand disponible."""
        # Créer ressource et créneau
        resource_response = await async_client.post("/resources", json=sample_resource_data)
        resource_id = resource_response.json()["id"]
        
        sample_availability_data["resource_id"] = resource_id
        await async_client.post(
            f"/resources/{resource_id}/availability",
            json=sample_availability_data
        )
        
        # Vérifier la disponibilité dans la plage
        start = datetime.fromisoformat(sample_availability_data["start_time"])
        check_start = start + timedelta(hours=1)
        check_end = check_start + timedelta(hours=2)
        
        response = await async_client.get(
            f"/resources/{resource_id}/availability/check",
            params={
                "start_time": check_start.isoformat(),
                "end_time": check_end.isoformat(),
                "quantity": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_available"] == True
    
    @pytest.mark.asyncio
    async def test_check_availability_with_quantity(
        self, async_client, sample_resource_data, sample_availability_data
    ):
        """Test la vérification avec quantité."""
        # Créer ressource
        resource_response = await async_client.post("/resources", json=sample_resource_data)
        resource_id = resource_response.json()["id"]
        
        # Créer créneau avec quantité=2
        sample_availability_data["resource_id"] = resource_id
        sample_availability_data["quantity"] = 2
        await async_client.post(
            f"/resources/{resource_id}/availability",
            json=sample_availability_data
        )
        
        # Vérifier avec quantity=2
        start = datetime.fromisoformat(sample_availability_data["start_time"])
        check_start = start + timedelta(hours=1)
        check_end = check_start + timedelta(hours=2)
        
        response = await async_client.get(
            f"/resources/{resource_id}/availability/check",
            params={
                "start_time": check_start.isoformat(),
                "end_time": check_end.isoformat(),
                "quantity": 2
            }
        )
        
        assert response.status_code == 200


class TestGetAvailabilitySlots:
    """Tests pour la récupération de créneaux."""
    
    def test_get_availability_slots(
        self, test_client, sample_resource_data, sample_availability_data
    ):
        """Test la récupération des créneaux."""
        # Créer ressource et créneau
        resource_response = test_client.post("/resources", json=sample_resource_data)
        resource_id = resource_response.json()["id"]
        
        sample_availability_data["resource_id"] = resource_id
        test_client.post(
            f"/resources/{resource_id}/availability",
            json=sample_availability_data
        )
        
        # Récupérer les créneaux
        start = datetime.fromisoformat(sample_availability_data["start_time"])
        end = datetime.fromisoformat(sample_availability_data["end_time"])
        
        response = test_client.get(
            f"/resources/{resource_id}/availability",
            params={
                "start_time": start.isoformat(),
                "end_time": end.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "available_slots" in data
        assert len(data["available_slots"]) > 0
