#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES FILES
Сервис для работы с файлами
=============================================================================
"""
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from loguru import logger

from app.core.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class FileService:
    """Сервис для операций с файлами."""

    ALLOWED_TYPES = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'video': ['video/mp4', 'video/webm', 'video/quicktime'],
        'audio': ['audio/mpeg', 'audio/ogg', 'audio/wav'],
        'document': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
    }

    def __init__(self):
        self.upload_folder = Path(settings.UPLOAD_FOLDER)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(
            self,
            file_content: bytes,
            filename: str,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Сохранение загруженного файла.
        
        Args:
            file_content: Содержимое файла
            filename: Имя файла
            
        Returns:
            Tuple[bool, str, Dict]: (успех, путь, метаданные)
        """
        try:
            # Проверка размера
            if len(file_content) > settings.MAX_FILE_SIZE:
                return False, "", {"error": f"Файл слишком большой (макс. {settings.MAX_FILE_SIZE / 1024 / 1024} MB)"}

            # Определение MIME типа
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Проверка типа файла
            file_category = mime_type.split('/')[0]
            if file_category not in self.ALLOWED_TYPES and mime_type not in sum(self.ALLOWED_TYPES.values(), []):
                return False, "", {"error": "Недопустимый тип файла"}

            # Генерация уникального имени
            ext = Path(filename).suffix or self._get_extension_from_mime(mime_type)
            unique_filename = f"{uuid.uuid4().hex}{ext}"

            # Создание подпапки по типу
            subfolder = self._get_subfolder_for_type(mime_type)
            file_path = self.upload_folder / subfolder / unique_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Сохранение файла
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Метаданные
            metadata = {
                "file_name": filename,
                "file_path": str(file_path.relative_to(self.upload_folder)),
                "file_type": mime_type,
                "file_size": len(file_content),
                "width": None,
                "height": None,
                "duration": None,
            }

            # Для изображений/видео можно добавить извлечение метаданных
            if file_category == 'image':
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        metadata["width"] = img.width
                        metadata["height"] = img.height
                except ImportError:
                    logger.warning("PIL не установлен, метаданные изображения не извлечены")
                except Exception as e:
                    logger.warning(f"Не удалось извлечь метаданные изображения: {e}")

            logger.info(f"✅ Файл сохранён: {file_path}")

            return True, str(file_path), metadata

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            return False, "", {"error": str(e)}

    def get_file_url(self, file_path: str) -> str:
        """
        Получение URL для файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: URL файла
        """
        return f"/api/files/{file_path}"

    def delete_file(self, file_path: str) -> bool:
        """
        Удаление файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            bool: True если успешно
        """
        try:
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
                logger.info(f"🗑️ Файл удалён: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла: {e}")
            return False

    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Получение расширения из MIME типа."""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'audio/mpeg': '.mp3',
            'application/pdf': '.pdf',
            'text/plain': '.txt',
        }
        return extensions.get(mime_type, '.bin')

    def _get_subfolder_for_type(self, mime_type: str) -> str:
        """Получение подпапки для типа файла."""
        file_category = mime_type.split('/')[0]

        if file_category == 'image':
            return 'images'
        elif file_category == 'video':
            return 'videos'
        elif file_category == 'audio':
            return 'audio'
        else:
            return 'documents'


# Глобальный экземпляр сервиса
file_service = FileService()