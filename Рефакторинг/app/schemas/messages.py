#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS MESSAGES
Pydantic схемы для работы с сообщениями
=============================================================================
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# =============================================================================
# ЗАПРОСЫ
# =============================================================================
class MessageRequest(BaseModel):
    """
    Схема запроса отправки сообщения.
    
    Attributes:
        content: Текст сообщения
        attachments: Вложения (опционально)
    """
    content: str = Field("", min_length=0, max_length=1000, description="Текст сообщения")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Вложения")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Привет, мир!",
                "attachments": [
                    {
                        "file_url": "/api/files/images/abc123.jpg",
                        "file_name": "photo.jpg",
                        "file_size": 102400,
                        "file_type": "image/jpeg"
                    }
                ]
            }
        }
    }


class MessageStatusUpdate(BaseModel):
    """
    Схема обновления статуса сообщения.
    
    Attributes:
        message_ids: Список ID сообщений
        sender_nickname: Никнейм получателя
    """
    message_ids: List[int] = Field(..., description="Список ID сообщений")
    sender_nickname: str = Field(..., description="Никнейм получателя")


# =============================================================================
# ОТВЕТЫ
# =============================================================================
class AttachmentResponse(BaseModel):
    """
    Схема ответа с информацией о вложении.
    
    Attributes:
        file_name: Имя файла
        file_url: URL файла
        file_size: Размер файла в байтах
        file_type: MIME тип
        width: Ширина (для изображений/видео)
        height: Высота (для изображений/видео)
        duration: Длительность в секундах (для видео/аудио)
    """
    file_name: str = Field(..., description="Имя файла")
    file_url: str = Field(..., description="URL файла")
    file_size: int = Field(..., description="Размер файла в байтах")
    file_type: str = Field(..., description="MIME тип")
    width: Optional[int] = Field(None, description="Ширина")
    height: Optional[int] = Field(None, description="Высота")
    duration: Optional[int] = Field(None, description="Длительность в секундах")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "file_name": "photo.jpg",
                "file_url": "/api/files/images/abc123.jpg",
                "file_size": 102400,
                "file_type": "image/jpeg",
                "width": 1920,
                "height": 1080,
                "duration": None
            }
        }
    }


class MessageResponse(BaseModel):
    """
    Схема ответа с информацией о сообщении.
    
    Attributes:
        id: ID сообщения
        nickname: Никнейм отправителя
        content: Текст сообщения
        channel: Название канала
        time: Время отправки
        sender_id: ID отправителя
        status: Статус доставки (sent/delivered/read)
        attachments: Вложения
    """
    id: int = Field(..., description="ID сообщения")
    nickname: str = Field(..., description="Никнейм отправителя")
    content: str = Field(..., description="Текст сообщения")
    channel: str = Field(..., description="Название канала")
    time: str = Field(..., description="Время отправки (ISO 8601)")
    sender_id: Optional[int] = Field(None, description="ID отправителя")
    status: str = Field("sent", description="Статус доставки")
    attachments: Optional[List[AttachmentResponse]] = Field(None, description="Вложения")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "nickname": "User123",
                "content": "Привет, мир!",
                "channel": "общий-чат",
                "time": "2024-01-15T12:30:00",
                "sender_id": 1,
                "status": "read",
                "attachments": []
            }
        }
    }


class MessageHistoryResponse(BaseModel):
    """
    Схема ответа с историей сообщений.
    
    Attributes:
        messages: Список сообщений
        channel: Название канала
        total: Общее количество сообщений
    """
    messages: List[MessageResponse] = Field(..., description="Список сообщений")
    channel: str = Field(..., description="Название канала")
    total: int = Field(..., description="Общее количество сообщений")

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "id": 1,
                        "nickname": "User123",
                        "content": "Привет!",
                        "channel": "общий-чат",
                        "time": "2024-01-15T12:30:00",
                        "sender_id": 1,
                        "status": "read",
                        "attachments": []
                    }
                ],
                "channel": "общий-чат",
                "total": 1
            }
        }
    }


class MessagesListResponse(BaseModel):
    """
    Схема ответа со списком сообщений (REST API).
    
    Attributes:
        messages: Список сообщений
    """
    messages: List[MessageResponse] = Field(..., description="Список сообщений")