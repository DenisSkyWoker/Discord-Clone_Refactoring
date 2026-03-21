#!/usr/bin/env python3
"""
=============================================================================
APP API FILES
API эндпоинты для работы с файлами
=============================================================================
"""
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from mimetypes import guess_type
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, get_current_user
from app.core.config import get_settings
from app.core.exceptions import ValidationException, NotFoundException, AuthorizationException
from app.db.models import Message, MessageAttachment
from app.db.session import AsyncSession
from app.schemas.files import FileUploadResponse, FileDeleteResponse
from app.services.files import file_service
from app.utils.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Роутер
router = APIRouter(tags=["Файлы"])


# =============================================================================
# ЗАГРУЗКА ФАЙЛА
# =============================================================================
@router.post("/upload", response_model=FileUploadResponse)
@limiter.limit("10/minute")
async def upload_file(
        request: Request,
        file: UploadFile = File(...),
        current_user: Dict[str, Any] = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Загрузка файла.
    
    - **file**: Файл для загрузки (макс. 10 MB)
    """
    try:
        # Чтение содержимого файла
        file_content = await file.read()
        filename = file.filename or "unknown"

        # Сохранение файла
        success, file_path, metadata = file_service.save_uploaded_file(
            file_content=file_content,
            filename=filename,
        )

        if not success:
            raise ValidationException(metadata.get('error', 'Ошибка загрузки'))

        return FileUploadResponse(
            success=True,
            file_url=file_service.get_file_url(file_path),
            file_name=metadata['file_name'],
            file_type=metadata['file_type'],
            file_size=metadata['file_size'],
            width=metadata['width'],
            height=metadata['height'],
            duration=metadata['duration'],
        )

    except ValidationException as e:
        logger.warning(f"⚠️ Ошибка загрузки файла: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке файла: {e}")
        raise ValidationException("Ошибка при загрузке файла")


# =============================================================================
# ПОЛУЧЕНИЕ ФАЙЛА
# =============================================================================
@router.get("/files/{file_path:path}")
async def get_file(file_path: str) -> FileResponse:
    """
    Получение файла по пути.
    """
    try:
        full_path = Path(settings.UPLOAD_FOLDER) / file_path

        if not full_path.exists():
            raise NotFoundException("Файл не найден")

        # Определение MIME типа
        mime_type, _ = guess_type(str(full_path))

        return FileResponse(
            str(full_path),
            media_type=mime_type or "application/octet-stream",
            filename=full_path.name,
        )

    except NotFoundException as e:
        logger.warning(f"⚠️ Файл не найден: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении файла: {e}")
        raise NotFoundException("Файл не найден")


# =============================================================================
# УДАЛЕНИЕ ФАЙЛА
# =============================================================================
@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file_endpoint(
        file_id: int,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> FileDeleteResponse:
    """
    Удаление файла.
    """
    try:
        attachment = await db.get(MessageAttachment, file_id)

        if not attachment:
            raise NotFoundException("Файл не найден")

        # Проверка прав
        message = await db.get(Message, attachment.message_id)

        if not message or message.user_id != current_user["user_id"]:
            raise AuthorizationException("Нет прав на удаление")

        # Удаление файла с диска
        file_service.delete_file(attachment.file_path)

        # Удаление записи из БД
        await db.delete(attachment)
        await db.commit()

        return FileDeleteResponse(
            message="Файл удалён",
            file_id=file_id,
        )

    except (NotFoundException, AuthorizationException) as e:
        logger.warning(f"⚠️ Ошибка удаления файла: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении файла: {e}")
        raise ValidationException("Ошибка при удалении файла")