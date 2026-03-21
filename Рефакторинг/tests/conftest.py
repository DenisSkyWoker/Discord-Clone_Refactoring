#!/usr/bin/env python3
"""
=============================================================================
TESTS CONFIG
Конфигурация pytest для Discord Clone
=============================================================================
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport

from app import app
from app.core.config import get_settings
from app.db.session import engine, async_session_maker
from app.db.models import Base


settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создание event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP клиент для тестирования API."""
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="function")
async def db_session():
    """Сессия базы данных для тестов."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_data() -> dict:
    """Данные тестового пользователя."""
    return {
        "nickname": "TestUser123",
        "email": "test@example.com",
        "password": "TestPass123!"
    }


@pytest.fixture
def test_channel_data() -> dict:
    """Данные тестового канала."""
    return {
        "name": "test-channel",
        "password": None
    }