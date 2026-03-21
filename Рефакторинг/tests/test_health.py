#!/usr/bin/env python3
"""
=============================================================================
TESTS HEALTH
Тесты здоровья сервера
=============================================================================
"""
import pytest
from httpx import AsyncClient


class TestHealth:
    """Тесты health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Тест проверки здоровья сервера."""
        response = await client.get("/health")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_root_redirect(self, client: AsyncClient):
        """Тест перенаправления с корня."""
        response = await client.get("/", follow_redirects=False)

        assert response.status_code in [200, 307]