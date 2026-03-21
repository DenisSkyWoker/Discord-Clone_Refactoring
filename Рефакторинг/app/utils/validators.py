#!/usr/bin/env python3
"""
=============================================================================
APP UTILS VALIDATORS
Валидаторы данных
=============================================================================
"""
import re
from typing import Tuple

from app.core.config import get_settings

settings = get_settings()


def validate_nickname(nickname: str) -> Tuple[bool, str]:
    """
    Валидация никнейма.
    
    Args:
        nickname: Никнейм для проверки
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение)
    """
    if not nickname or len(nickname) < 3:
        return False, "Никнейм должен быть не менее 3 символов"

    if len(nickname) > 50:
        return False, "Никнейм не должен превышать 50 символов"

    if not re.match(r"^[a-zA-Zа-яА-Я0-9_]+$", nickname):
        return False, "Никнейм может содержать только буквы, цифры и подчёркивание"

    return True, "Никнейм валиден"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Валидация email.
    
    Args:
        email: Email для проверки
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение)
    """
    if not email:
        return False, "Email обязателен"

    email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_pattern, email):
        return False, "Неверный формат email"

    if len(email) > 100:
        return False, "Email не должен превышать 100 символов"

    return True, "Email валиден"


def validate_channel_name(name: str) -> Tuple[bool, str]:
    """
    Валидация названия канала.
    
    Args:
        name: Название канала
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение)
    """
    if not name or len(name) < 3:
        return False, "Название канала должно быть не менее 3 символов"

    if len(name) > 25:
        return False, "Название канала не должно превышать 25 символов"

    if not re.search(r"[a-zA-Zа-яА-Я]", name):
        return False, "Название должно содержать хотя бы одну букву"

    if not re.match(r"^[a-zA-Zа-яА-Я0-9_-]+$", name):
        return False, "Только буквы, цифры, дефис и подчёркивание"

    if re.match(r"^[0-9_-]", name):
        return False, "Название должно начинаться с буквы"

    reserved_names = [
        "общий-чат", "флудилка", "мемы",
        "Администраторы", "администраторы", "admin", "mod"
    ]
    if name.lower() in reserved_names:
        return False, "Это название зарезервировано"

    return True, "Название канала валидно"


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