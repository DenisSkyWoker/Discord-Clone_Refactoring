#!/usr/bin/env python3
"""
=============================================================================
APP API PROFILE
API эндпоинты управления профилем
=============================================================================
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, get_current_user
from app.core.exceptions import ValidationException, NotFoundException
from app.db.session import AsyncSession
from app.schemas.profile import (
    ProfileUpdateRequest,
    ProfileUpdateResponse,
    ProfileStatsResponse,
    ProfileDeleteResponse,
)
from app.services.auth import AuthService
from app.services.messages import MessageService
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Роутер
router = APIRouter(prefix="/profile", tags=["Профиль"])


# =============================================================================
# СТАТИСТИКА ПРОФИЛЯ
# =============================================================================
@router.get("/stats", response_model=ProfileStatsResponse)
async def get_profile_stats(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ProfileStatsResponse:
    """
    Получение статистики профиля.
    """
    message_service = MessageService(db)

    try:
        stats = await message_service.get_profile_stats(user_id=current_user["user_id"])

        return ProfileStatsResponse(
            messages_count=stats["messages_count"],
            channels_count=stats["channels_count"],
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return ProfileStatsResponse(messages_count=0, channels_count=0)


# =============================================================================
# ОБНОВЛЕНИЕ ПРОФИЛЯ
# =============================================================================
@router.put("/auth/profile", response_model=ProfileUpdateResponse)
@limiter.limit("5/minute")
async def update_profile(
        request: Request,
        data: ProfileUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ProfileUpdateResponse:
    """
    Обновить данные профиля.
    """
    auth_service = AuthService(db)

    try:
        result = await auth_service.update_profile(
            user_id=current_user["user_id"],
            nickname=data.nickname,
            email=data.email,
        )

        return ProfileUpdateResponse(
            message=result["message"],
            nickname=result["nickname"],
            email=result["email"],
            email_verification_sent=result["email_verification_sent"],
        )

    except (ValidationException, NotFoundException) as e:
        logger.warning(f"⚠️ Ошибка обновления профиля: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении профиля: {e}")
        raise ValidationException("Ошибка при обновлении профиля")