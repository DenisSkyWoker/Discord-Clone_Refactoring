#!/usr/bin/env python3
"""
Discord Clone Application
"""
from fastapi import FastAPI
from app.core.config import get_settings
from app.core.lifespan import lifespan

settings = get_settings()

# Создание приложения
app = FastAPI(
    title=settings.APP_NAME,
    description="Discord Clone API",
    version="1.0.0",
    lifespan=lifespan,
)

# Импорт роутеров (после создания app для избежания циклических импортов)
from app.api import auth, channels, messages, files, profile, websocket

# Регистрация роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Авторизация"])
app.include_router(channels.router, prefix="/api/channels", tags=["Каналы"])
app.include_router(messages.router, prefix="/api/messages", tags=["Сообщения"])
app.include_router(files.router, prefix="/api", tags=["Файлы"])
app.include_router(profile.router, prefix="/api", tags=["Профиль"])
app.include_router(websocket.router, tags=["WebSocket"])

# Импорт middleware
from app.core.middleware import setup_middleware
setup_middleware(app)

__all__ = ["app"]