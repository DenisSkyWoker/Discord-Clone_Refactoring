#!/usr/bin/env python3
"""
=============================================================================
APP API CHANNELS
API эндпоинты управления каналами
=============================================================================
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, get_current_user, get_client_ip
from app.core.exceptions import ValidationException, NotFoundException, AuthorizationException
from app.db.models import Channel
from app.db.session import AsyncSession
from app.schemas.channels import (
    CreateChannelRequest,
    JoinChannelRequest,
    ChannelResponse,
    ChannelListResponse,
    ChannelDeleteResponse,
)
from app.services.auth import AuthService
from app.services.websocket_manager import manager
from app.utils.logging import get_logger
from app.core.security import verify_password, get_password_hash
from sqlalchemy import select

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Роутер
router = APIRouter(prefix="/channels", tags=["Каналы"])


# =============================================================================
# ПОЛУЧИТЬ КАНАЛЫ
# =============================================================================
@router.get("", response_model=ChannelListResponse)
async def get_channels(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ChannelListResponse:
    """
    Получить список всех доступных каналов.
    """
    try:
        # Системные каналы
        default_channels = [
            ChannelResponse(id=0, name="общий-чат", is_default=True, has_password=False),
            ChannelResponse(id=0, name="флудилка", is_default=True, has_password=False),
            ChannelResponse(id=0, name="мемы", is_default=True, has_password=False),
        ]

        # Пользовательские каналы
        result = await db.execute(select(Channel).where(Channel.is_active == True))
        custom_channels = result.scalars().all()

        for ch in custom_channels:
            default_channels.append(
                ChannelResponse(
                    id=ch.id,
                    name=ch.name,
                    is_default=False,
                    has_password=ch.password_hash is not None,
                    creator_id=ch.creator_id,
                )
            )

        return ChannelListResponse(channels=default_channels)

    except Exception as e:
        logger.error(f"❌ Ошибка получения каналов: {e}")
        return ChannelListResponse(channels=[])


# =============================================================================
# СОЗДАТЬ КАНАЛ
# =============================================================================
@router.post("/create", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_channel(
        request: Request,
        data: CreateChannelRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Создать новый канал с паролем.
    """
    client_ip = get_client_ip(request)

    try:
        # Проверка существования
        result = await db.execute(select(Channel).where(Channel.name == data.name))
        existing = result.scalar_one_or_none()

        if existing:
            raise ValidationException("Канал с таким названием уже существует")

        # Создание канала
        new_channel = Channel(
            name=data.name,
            password_hash=get_password_hash(data.password) if data.password else None,
            creator_id=current_user["user_id"],
        )

        db.add(new_channel)
        await db.commit()
        await db.refresh(new_channel)

        # Добавление в менеджер WebSocket
        await manager.add_channel(data.name)

        logger.info(f"✅ Создан канал: {data.name} (ID: {new_channel.id})")

        return {
            "message": "Канал создан",
            "channel_id": new_channel.id,
            "channel_name": new_channel.name,
        }

    except ValidationException as e:
        logger.warning(f"⚠️ Ошибка создания канала: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при создании канала: {e}")
        raise ValidationException("Ошибка при создании канала")


# =============================================================================
# ВОЙТИ В КАНАЛ
# =============================================================================
@router.post("/join", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def join_channel(
        request: Request,
        data: JoinChannelRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Присоединиться к защищённому каналу.
    """
    try:
        result = await db.execute(select(Channel).where(Channel.name == data.name))
        channel = result.scalar_one_or_none()

        if not channel:
            raise NotFoundException("Канал не найден")

        if channel.password_hash:
            if not data.password:
                raise ValidationException("Требуется пароль")

            if not verify_password(data.password, channel.password_hash):
                raise ValidationException("Неверный пароль")

        logger.info(f"✅ Пользователь {current_user['nickname']} присоединился к каналу {data.name}")

        return {"message": "Успешный вход", "channel_name": data.name}

    except (ValidationException, NotFoundException) as e:
        logger.warning(f"⚠️ Ошибка входа в канал: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при входе в канал: {e}")
        raise ValidationException("Ошибка при входе в канал")


# =============================================================================
# УДАЛИТЬ КАНАЛ
# =============================================================================
@router.delete("/{channel_id}", response_model=ChannelDeleteResponse)
async def delete_channel(
        channel_id: int,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ChannelDeleteResponse:
    """
    Удалить канал (только создатель).
    """
    try:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()

        if not channel:
            raise NotFoundException("Канал не найден")

        if channel.creator_id != current_user["user_id"]:
            raise AuthorizationException("Только создатель может удалить канал")

        channel.is_active = False
        await db.commit()

        logger.info(f"✅ Удалён канал: {channel.name}")

        return ChannelDeleteResponse(
            message="Канал удалён",
            channel_name=channel.name,
        )

    except (NotFoundException, AuthorizationException) as e:
        logger.warning(f"⚠️ Ошибка удаления канала: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении канала: {e}")
        raise ValidationException("Ошибка при удалении канала")