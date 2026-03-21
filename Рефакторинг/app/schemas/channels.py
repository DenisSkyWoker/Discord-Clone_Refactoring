#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS CHANNELS
Pydantic схемы для управления каналами
=============================================================================
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

import re


# =============================================================================
# ЗАПРОСЫ
# =============================================================================
class CreateChannelRequest(BaseModel):
    """
    Схема запроса создания канала.
    
    Attributes:
        name: Название канала (3-25 символов)
        password: Пароль канала (опционально)
    """
    name: str = Field(..., min_length=3, max_length=25, description="Название канала")
    password: Optional[str] = Field(None, min_length=4, description="Пароль канала")

    @field_validator("name")
    @classmethod
    def validate_channel_name(cls, v: str) -> str:
        """Валидация названия канала."""
        v = v.strip()

        if not re.search(r"[a-zA-Zа-яА-Я]", v):
            raise ValueError("Название должно содержать хотя бы одну букву")

        if not re.match(r"^[a-zA-Zа-яА-Я0-9_-]+$", v):
            raise ValueError("Только буквы, цифры, дефис и подчёркивание")

        if re.match(r"^[0-9_-]", v):
            raise ValueError("Название должно начинаться с буквы")

        reserved_names = [
            "общий-чат", "флудилка", "мемы",
            "администраторы", "admin", "mod", "модератор"
        ]
        if v.lower() in reserved_names:
            raise ValueError("Это название зарезервировано")

        return v


class JoinChannelRequest(BaseModel):
    """
    Схема запроса входа в защищённый канал.
    
    Attributes:
        name: Название канала
        password: Пароль канала
    """
    name: str = Field(..., min_length=1, max_length=50, description="Название канала")
    password: str = Field(..., min_length=1, description="Пароль канала")


# =============================================================================
# ОТВЕТЫ
# =============================================================================
class ChannelResponse(BaseModel):
    """
    Схема ответа с информацией о канале.
    
    Attributes:
        id: ID канала
        name: Название канала
        is_default: Системный канал
        has_password: Защищён паролем
        creator_id: ID создателя (для пользовательских каналов)
    """
    id: int = Field(..., description="ID канала")
    name: str = Field(..., description="Название канала")
    is_default: bool = Field(False, description="Системный канал")
    has_password: bool = Field(False, description="Защищён паролем")
    creator_id: Optional[int] = Field(None, description="ID создателя")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "общий-чат",
                "is_default": True,
                "has_password": False,
                "creator_id": None
            }
        }
    }


class ChannelListResponse(BaseModel):
    """
    Схема ответа со списком каналов.
    
    Attributes:
        channels: Список каналов
    """
    channels: List[ChannelResponse] = Field(..., description="Список каналов")

    model_config = {
        "json_schema_extra": {
            "example": {
                "channels": [
                    {
                        "id": 0,
                        "name": "общий-чат",
                        "is_default": True,
                        "has_password": False
                    },
                    {
                        "id": 1,
                        "name": "мой-канал",
                        "is_default": False,
                        "has_password": True,
                        "creator_id": 1
                    }
                ]
            }
        }
    }


class ChannelDeleteResponse(BaseModel):
    """
    Схема ответа при удалении канала.
    
    Attributes:
        message: Сообщение
        channel_name: Название удалённого канала
    """
    message: str = Field(..., description="Сообщение")
    channel_name: Optional[str] = Field(None, description="Название канала")