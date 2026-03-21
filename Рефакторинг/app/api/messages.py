#!/usr/bin/env python3
"""
=============================================================================
APP API MESSAGES
API эндпоинты для работы с сообщениями
=============================================================================
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.db.models import Message
from app.db.session import AsyncSession
from app.schemas.messages import MessageResponse, MessagesListResponse
from app.services.messages import MessageService
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Роутер
router = APIRouter(prefix="/messages", tags=["Сообщения"])


# =============================================================================
# ПОЛУЧИТЬ СООБЩЕНИЯ
# =============================================================================
@router.get("/{channel}", response_model=MessagesListResponse)
async def get_messages(
        channel: str,
        limit: int = Query(50, ge=1, le=100),
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> MessagesListResponse:
    """
    Получение истории сообщений канала.
    
    - **channel**: Название канала
    - **limit**: Лимит сообщений (1-100)
    """
    message_service = MessageService(db)

    try:
        messages = await message_service.get_channel_messages(
            channel=channel,
            user_id=current_user["user_id"],
            limit=limit,
        )

        return MessagesListResponse(
            messages=messages,
            channel=channel,
            total=len(messages),
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения сообщений: {e}")
        return MessagesListResponse(messages=[], channel=channel, total=0)


# =============================================================================
# ОНЛАЙН ПОЛЬЗОВАТЕЛИ
# =============================================================================
@router.get("/online/{channel}", response_model=Dict[str, Any])
async def get_online_users(
        channel: str,
) -> Dict[str, Any]:
    """
    Получение списка онлайн пользователей канала.
    """
    from app.services.websocket_manager import manager

    users = manager.get_online_users(channel)

    return {
        "users": users,
        "channel": channel,
        "count": len(users),
    }