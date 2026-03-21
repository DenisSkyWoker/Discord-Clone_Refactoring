#!/usr/bin/env python3
"""
=============================================================================
TESTS CHANNELS
Тесты управления каналами
=============================================================================
"""
import pytest
from httpx import AsyncClient


class TestChannels:
    """Тесты каналов."""

    @pytest.fixture
    async def auth_token(self, client: AsyncClient, test_user_data: dict) -> str:
        """Получение токена авторизации."""
        reg_response = await client.post("/api/auth/register", json=test_user_data)
        return reg_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_channels(self, client: AsyncClient, auth_token: str):
        """Тест получения списка каналов."""
        response = await client.get(
            "/api/channels",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert len(data["channels"]) >= 3  # Минимум 3 системных канала

    @pytest.mark.asyncio
    async def test_create_channel(self, client: AsyncClient, auth_token: str, test_channel_data: dict):
        """Тест создания канала."""
        response = await client.post(
            "/api/channels/create",
            json=test_channel_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "channel_id" in data
        assert data["channel_name"] == test_channel_data["name"]

    @pytest.mark.asyncio
    async def test_create_channel_invalid_name(self, client: AsyncClient, auth_token: str):
        """Тест создания канала с невалидным именем."""
        response = await client.post(
            "/api/channels/create",
            json={"name": "123", "password": None},  # Только цифры
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_channel(self, client: AsyncClient, auth_token: str, test_channel_data: dict):
        """Тест удаления канала."""
        # Создание
        create_response = await client.post(
            "/api/channels/create",
            json=test_channel_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        channel_id = create_response.json()["channel_id"]

        # Удаление
        delete_response = await client.delete(
            f"/api/channels/{channel_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_response.status_code == 200