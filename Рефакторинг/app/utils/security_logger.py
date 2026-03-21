#!/usr/bin/env python3
"""
=============================================================================
APP UTILS SECURITY LOGGER
Логирование событий безопасности
=============================================================================
"""
from typing import Any, Dict, Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)


def log_security_event(
        event_type: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        ip_address: str = "unknown"
) -> None:
    """
    Логирование события безопасности.
    
    Args:
        event_type: Тип события (LOGIN_SUCCESS, LOGIN_FAILED, etc.)
        details: Детали события
        user_id: ID пользователя (опционально)
        ip_address: IP адрес (опционально)
    """
    # Не логируем чувствительные данные
    safe_details = {
        k: v for k, v in details.items()
        if k not in ['password', 'token', 'secret', 'code']
    }

    logger.info(
        f"🔒 [SECURITY] {event_type} | "
        f"user_id={user_id} | "
        f"ip={ip_address} | "
        f"details={safe_details}"
    )