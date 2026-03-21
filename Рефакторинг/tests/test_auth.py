#!/usr/bin/env python3
"""
=============================================================================
TESTS AUTH
Тесты модуля авторизации
=============================================================================
"""
import pytest
from httpx import AsyncClient


class TestAuth:
    """Тесты авторизации и регистрации."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, test_user_data: dict):
        """Тест успешной регистрации."""
        response = await client.post(
            "/api/auth/register",
            json=test_user_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] > 0
        assert data["nickname"] == test_user_data["nickname"]
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_nickname(self, client: AsyncClient, test_user_data: dict):
        """Тест регистрации с дублирующимся никнеймом."""
        # Первая регистрация
        await client.post("/api/auth/register", json=test_user_data)

        # Вторая регистрация с тем же ником
        response = await client.post(
            "/api/auth/register",
            json=test_user_data
        )

        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data: dict):
        """Тест успешного входа."""
        # Регистрация
        await client.post("/api/auth/register", json=test_user_data)

        # Вход
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["nickname"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: dict):
        """Тест входа с неверным паролем."""
        # Регистрация
        await client.post("/api/auth/register", json=test_user_data)

        # Вход с неверным паролем
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["nickname"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me(self, client: AsyncClient, test_user_data: dict):
        """Тест получения текущего пользователя."""
        # Регистрация и получение токена
        reg_response = await client.post("/api/auth/register", json=test_user_data)
        token = reg_response.json()["access_token"]

        # Получение профиля
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == test_user_data["nickname"]
        assert data["email"] == test_user_data["email"]