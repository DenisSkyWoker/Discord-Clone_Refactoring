#!/usr/bin/env python3
"""
=============================================================================
APP API INIT
Экспорт API роутеров
=============================================================================
"""
from app.api.auth import router as auth_router
from app.api.channels import router as channels_router
from app.api.messages import router as messages_router
from app.api.files import router as files_router
from app.api.profile import router as profile_router
from app.api.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "channels_router",
    "messages_router",
    "files_router",
    "profile_router",
    "websocket_router",
]