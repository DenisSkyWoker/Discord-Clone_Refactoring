#!/usr/bin/env python3
"""
=============================================================================
APP DB INIT
Экспорт модуля базы данных
=============================================================================
"""
from app.db.session import (
    engine,
    async_session_maker,
    get_db,
    init_database,
    dispose_database,
)
from app.db.models import (
    Base,
    RegisteredUser,
    EmailVerificationCode,
    PasswordResetToken,
    ConnectedUser,
    Message,
    MessageStatus,
    Channel,
    SecurityLog,
    MessageAttachment,
)
from app.db.health import check_database_health
from app.db.migrations import run_migrations

__all__ = [
    "engine",
    "async_session_maker",
    "get_db",
    "init_database",
    "dispose_database",
    "Base",
    "RegisteredUser",
    "EmailVerificationCode",
    "PasswordResetToken",
    "ConnectedUser",
    "Message",
    "MessageStatus",
    "Channel",
    "SecurityLog",
    "MessageAttachment",
    "check_database_health",
    "run_migrations",
]