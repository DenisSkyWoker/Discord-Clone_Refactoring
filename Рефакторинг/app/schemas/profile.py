#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS PROFILE
Pydantic схемы для управления профилем
=============================================================================
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator

import re


# =============================================================================
# ЗАПРОСЫ
# =============================================================================
class ProfileUpdateRequest(BaseModel):
    """
    Схема запроса обновления профиля.
    
    Attributes:
        nickname: Новый никнейм (3-50 символов)
        email: Новый email (опционально)
    """
    nickname: str = Field(..., min_length=3, max_length=50, description="Никнейм")
    email: Optional[str] = Field(None, description="Email адрес")

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        """Валидация никнейма."""
        v = v.strip()

        if not re.match(r"^[a-zA-Zа-яА-Я0-9_]+$", v):
            raise ValueError("Никнейм может содержать только буквы, цифры и подчёркивание")

        reserved_names = ["admin", "mod", "administrator", "модератор", "админ"]
        if v.lower() in reserved_names:
            raise ValueError("Этот никнейм зарезервирован")

        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Валидация email."""
        if v is None:
            return None
        v = v.strip()
        if len(v) == 0:
            return None
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Неверный формат email")
        return v.lower()


class DeleteAccountRequest(BaseModel):
    """
    Схема запроса удаления аккаунта.
    
    Attributes:
        confirm_nickname: Никнейм для подтверждения
    """
    confirm_nickname: str = Field(..., min_length=1, description="Никнейм для подтверждения")


# =============================================================================
# ОТВЕТЫ
# =============================================================================
class ProfileStatsResponse(BaseModel):
    """
    Схема ответа со статистикой профиля.
    
    Attributes:
        messages_count: Количество сообщений
        channels_count: Количество созданных каналов
    """
    messages_count: int = Field(..., description="Количество сообщений")
    channels_count: int = Field(..., description="Количество созданных каналов")

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages_count": 150,
                "channels_count": 5
            }
        }
    }


class ProfileUpdateResponse(BaseModel):
    """
    Схема ответа при обновлении профиля.
    
    Attributes:
        message: Сообщение
        nickname: Обновлённый никнейм
        email: Обновлённый email
        email_verification_sent: Отправлен ли код подтверждения
    """
    message: str = Field(..., description="Сообщение")
    nickname: str = Field(..., description="Никнейм")
    email: Optional[str] = Field(None, description="Email")
    email_verification_sent: bool = Field(False, description="Код подтверждения отправлен")


class ProfileDeleteResponse(BaseModel):
    """
    Схема ответа при удалении аккаунта.
    
    Attributes:
        message: Сообщение
    """
    message: str = Field(..., description="Сообщение")