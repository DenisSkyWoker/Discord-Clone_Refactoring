#!/usr/bin/env python3
"""
События запуска и остановки приложения
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from app.core.config import get_settings
from app.db.session import init_database, dispose_database
from app.db.health import check_database_health
from app.db.migrations import run_migrations
from app.services.websocket_manager import manager
from auth import init_auth_dependencies
from models import (
    RegisteredUser,
    EmailVerificationCode,
    ConnectedUser,
    Message,
    Channel,
    SecurityLog,
)
from utils import log_security_event

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator:
    """События при запуске и остановке приложения."""

    # === ЗАПУСК ===
    logger.info("🚀 Запуск приложения...")

    # Проверка здоровья БД
    logger.info("🔍 Проверка подключения к базе данных...")
    health = await check_database_health()

    if not health["success"]:
        logger.error("🛑 Сервер не может быть запущен без подключения к базе данных!")
        logger.error(f"❌ Ошибки: {health.get('errors', [])}")
        raise RuntimeError("Database connection failed")

    logger.success("✅ База данных готова к работе!")

    # Применение миграций
    logger.info("🔧 Применение миграций...")
    await run_migrations()
    logger.success("✅ Миграции применены!")

    # Инициализация зависимостей auth
    logger.info("🔐 Инициализация модуля авторизации...")
    from app.db.session import async_session_maker
    init_auth_dependencies(
        session_maker=async_session_maker,
        reg_user=RegisteredUser,
        email_code=EmailVerificationCode,
        conn_user=ConnectedUser,
        msg=Message,
        ch=Channel,
        sec_log=SecurityLog,
        cfg=settings,
        log_sec=log_security_event,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.info("✅ Сервер запущен и готов к работе!")

    yield

    # === ОСТАНОВКА ===
    logger.info("👋 Остановка приложения...")

    # Закрытие WebSocket подключений
    logger.info("🔌 Закрытие WebSocket подключений...")
    await manager.shutdown()

    # Закрытие соединений с БД
    logger.info("💾 Закрытие соединений с базой данных...")
    await dispose_database()

    logger.success("✅ Приложение остановлено")