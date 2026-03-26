"""Tests pour les endpoints de ressources."""
import pytest


class TestCreateResource:
    """Tests pour la creation de ressources."""

    @pytest.mark.asyncio
    async def test_create_resource_success(self, async_client, sample_resource_data):
        """Test la creation reussie d'une ressource."""
        response = await async_client.post('/resources', json=sample_resource_data)
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == sample_resource_data['name']
        assert data['type'] == sample_resource_data['type']
        assert data['capacity'] == sample_resource_data['capacity']
        assert 'id' in data
        assert data['is_active'] is True

    @pytest.mark.asyncio
    async def test_create_resource_missing_name(self, async_client):
        """Test la creation avec nom manquant."""
        data = {
            'type': 'HOTEL_ROOM',
            'description': 'Test',
            'capacity': 10,
            'location': 'Test',
            'price': 50.0,
        }
        response = await async_client.post('/resources', json=data)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_resource_invalid_capacity(self, async_client):
        """Test la creation avec capacite invalide."""
        data = {
            'name': 'Test',
            'type': 'HOTEL_ROOM',
            'description': 'Test',
            'capacity': -1,
            'location': 'Test',
            'price': 50.0,
        }
        response = await async_client.post('/resources', json=data)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_resource_invalid_type(self, async_client):
        """Test avec type invalide."""
        data = {
            'name': 'Test',
            'type': 'invalid_type',
            'description': 'Test',
            'capacity': 10,
            'location': 'Test',
            'price': 50.0,
        }
        response = await async_client.post('/resources', json=data)
        assert response.status_code in [400, 422]


class TestGetResource:
    """Tests pour la recuperation de ressources."""

    @pytest.mark.asyncio
    async def test_get_resource_success(self, async_client, sample_resource_data):
        """Test la recuperation d'une ressource."""
        create_response = await async_client.post('/resources', json=sample_resource_data)
        resource_id = create_response.json()['id']
        get_response = await async_client.get(f'/resources/{resource_id}')
        assert get_response.status_code == 200
        data = get_response.json()
        assert data['id'] == resource_id
        assert data['name'] == sample_resource_data['name']

    @pytest.mark.asyncio
    async def test_get_resource_not_found(self, async_client):
        """Test la recuperation d'une ressource inexistante."""
        fake_id = '00000000-0000-0000-0000-000000000000'
        response = await async_client.get(f'/resources/{fake_id}')
        assert response.status_code == 404


class TestListResources:
    """Tests pour la liste des ressources."""

    @pytest.mark.asyncio
    async def test_list_resources_empty(self, async_client):
        """Test la liste vide."""
        response = await async_client.get('/resources')
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_resources_with_items(self, async_client, sample_resource_data):
        """Test la liste avec ressources."""
        await async_client.post('/resources', json=sample_resource_data)
        await async_client.post('/resources', json={
            'name': 'Table T12',
            'type': 'RESTAURANT_TABLE',
            'description': 'Table terrasse',
            'capacity': 4,
            'location': 'Restaurant UrbanHub',
            'price': 0.0,
        })
        response = await async_client.get('/resources')
        assert response.status_code == 200
        assert len(response.json()) >= 2

    @pytest.mark.asyncio
    async def test_list_resources_by_type(self, async_client, sample_resource_data):
        """Test la liste filtree par type."""
        await async_client.post('/resources', json=sample_resource_data)
        response = await async_client.get('/resources?type=HOTEL_ROOM')
        assert response.status_code == 200
        resources = response.json()
        assert all(r['type'] == 'HOTEL_ROOM' for r in resources)


class TestUpdateResource:
    """Tests pour la mise a jour de ressources."""

    @pytest.mark.asyncio
    async def test_update_resource_success(self, async_client, sample_resource_data):
        """Test la mise a jour reussie."""
        create_response = await async_client.post('/resources', json=sample_resource_data)
        resource_id = create_response.json()['id']
        update_data = {'name': 'Nouveau Nom', 'price': 200.0, 'type': 'VENUE'}
        update_response = await async_client.put(f'/resources/{resource_id}', json=update_data)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data['name'] == 'Nouveau Nom'
        assert data['price'] == 200.0
        assert data['type'] == 'VENUE'


class TestDeactivateResource:
    """Tests pour la desactivation."""

    @pytest.mark.asyncio
    async def test_deactivate_resource(self, async_client, sample_resource_data):
        """Test la desactivation d'une ressource."""
        create_response = await async_client.post('/resources', json=sample_resource_data)
        resource_id = create_response.json()['id']
        response = await async_client.post(f'/resources/{resource_id}/deactivate')
        assert response.status_code == 200
        assert response.json()['is_active'] is False


class TestActivateResource:
    """Tests pour l'activation."""

    def test_activate_resource(self, test_client, sample_resource_data):
        """Test l'activation d'une ressource."""
        create_response = test_client.post('/resources', json=sample_resource_data)
        resource_id = create_response.json()['id']
        test_client.post(f'/resources/{resource_id}/deactivate')
        response = test_client.post(f'/resources/{resource_id}/activate')
        assert response.status_code == 200
        assert response.json()['is_active'] is True
