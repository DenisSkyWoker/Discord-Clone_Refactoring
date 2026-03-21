#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES INIT
Экспорт сервисных модулей
=============================================================================
"""
from app.services.email import send_verification_email
from app.services.websocket_manager import manager, ConnectionManager
from app.services.auth import AuthService
from app.services.messages import MessageService
from app.services.files import FileService

__all__ = [
    "send_verification_email",
    "manager",
    "ConnectionManager",
    "AuthService",
    "MessageService",
    "FileService",
]