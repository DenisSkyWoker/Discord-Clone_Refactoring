#!/usr/bin/env python3
"""
=============================================================================
APP UTILS HELPERS
Вспомогательные функции
=============================================================================
"""
import re
from datetime import datetime, timezone
from typing import Tuple, Any, Dict
from html import escape

from app.core.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def to_db_datetime(dt: datetime) -> datetime:
    """
    Конвертация datetime в формат без timezone для БД.
    
    Args:
        dt: datetime объект
        
    Returns:
        datetime: datetime без timezone
    """
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def sanitize_input(text: str) -> str:
    """
    Очистка пользовательского ввода от опасных символов.
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    # HTML экранирование
    text = escape(text)
    # Удаление потенциально опасных символов
    text = re.sub(r'[<>\"\'\\;]', '', text)
    return text.strip()


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Проверка сложности пароля.
    
    Args:
        password: Пароль для проверки
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение)
    """
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return False, f"Пароль должен быть не менее {settings.MIN_PASSWORD_LENGTH} символов"

    if not re.search(r"[A-Z]", password):
        return False, "Пароль должен содержать заглавные буквы"

    if not re.search(r"[a-z]", password):
        return False, "Пароль должен содержать строчные буквы"

    if not re.search(r"\d", password):
        return False, "Пароль должен содержать цифры"

    if settings.REQUIRE_SPECIAL_CHARS and not re.search(r"[!@#$%^&*()?]", password):
        return False, "Пароль должен содержать специальные символы"

    return True, "Пароль соответствует требованиям"


def generate_verification_code() -> str:
    """
    Генерация 6-значного кода верификации.
    
    Returns:
        str: 6-значный код
    """
    import secrets
    return "".join([str(secrets.randbelow(10)) for _ in range(6)])


def log_security_event(
        event_type: str,
        details: Dict[str, Any],
        user_id: int = None,
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
    logger.info(
        f"🔒 [SECURITY] {event_type} | "
        f"user_id={user_id} | "
        f"ip={ip_address} | "
        f"details={details}"
    )