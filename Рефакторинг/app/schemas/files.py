#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS FILES
Pydantic схемы для работы с файлами
=============================================================================
"""
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# ОТВЕТЫ
# =============================================================================
class FileUploadResponse(BaseModel):
    """
    Схема ответа при загрузке файла.
    
    Attributes:
        success: Успешность загрузки
        file_url: URL файла
        file_name: Имя файла
        file_type: MIME тип
        file_size: Размер файла в байтах
        width: Ширина (для изображений/видео)
        height: Высота (для изображений/видео)
        duration: Длительность (для видео/аудио)
    """
    success: bool = Field(True, description="Успешность загрузки")
    file_url: str = Field(..., description="URL файла")
    file_name: str = Field(..., description="Имя файла")
    file_type: str = Field(..., description="MIME тип")
    file_size: int = Field(..., description="Размер файла в байтах")
    width: Optional[int] = Field(None, description="Ширина")
    height: Optional[int] = Field(None, description="Высота")
    duration: Optional[int] = Field(None, description="Длительность в секундах")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "file_url": "/api/files/images/abc123.jpg",
                "file_name": "photo.jpg",
                "file_type": "image/jpeg",
                "file_size": 102400,
                "width": 1920,
                "height": 1080,
                "duration": None
            }
        }
    }


class FileDeleteResponse(BaseModel):
    """
    Схема ответа при удалении файла.
    
    Attributes:
        message: Сообщение
        file_id: ID удалённого файла
    """
    message: str = Field(..., description="Сообщение")
    file_id: Optional[int] = Field(None, description="ID файла")