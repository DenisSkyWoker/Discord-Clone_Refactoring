#!/usr/bin/env python3
"""
=============================================================================
APP DB SESSION
Сессии базы данных SQLAlchemy
=============================================================================
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from app.core.config import get_settings

settings = get_settings()

# =============================================================================
# ДВИЖОК БАЗЫ ДАННЫХ
# =============================================================================
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# =============================================================================
# ФАБРИКА СЕССИЙ
# =============================================================================
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# =============================================================================
# ЗАВИСИМОСТЬ ДЛЯ ПОЛУЧЕНИЯ СЕССИИ
# =============================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД.
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# =============================================================================
async def init_database() -> None:
    """Инициализация базы данных (создание таблиц)."""
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# =============================================================================
# ЗАКРЫТИЕ СОЕДИНЕНИЙ
# =============================================================================
async def dispose_database() -> None:
    """Закрытие соединений с базой данных."""
    await engine.dispose()