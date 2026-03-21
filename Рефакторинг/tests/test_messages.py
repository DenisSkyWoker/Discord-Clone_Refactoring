#!/usr/bin/env python3
"""
=============================================================================
TESTS MESSAGES
Тесты сообщений
=============================================================================
"""
import pytest
from httpx import AsyncClient


class TestMessages:
    """Тесты сообщений."""

    @pytest.fixture
    async def auth_token(self, client: AsyncClient, test_user_data: dict) -> str:
        """Получение токена авторизации."""
        reg_response = await client.post("/api/auth/register", json=test_user_data)
        return reg_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_messages(self, client: AsyncClient, auth_token: str):
        """Тест получения сообщений канала."""
        response = await client.get(
            "/api/messages/общий-чат",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_online_users(self, client: AsyncClient, auth_token: str):
        """Тест получения онлайн пользователей."""
        response = await client.get(
            "/api/online/общий-чат",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "channel" in data