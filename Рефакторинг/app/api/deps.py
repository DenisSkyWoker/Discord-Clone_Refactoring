#!/usr/bin/env python3
"""
=============================================================================
APP API DEPS
Зависимости FastAPI для API эндпоинтов
=============================================================================
"""
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_token
from app.core.exceptions import AuthenticationException
from app.db.session import async_session_maker, AsyncSession
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД.
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Получение текущего пользователя из JWT токена.
    
    Args:
        token: JWT токен
        db: Сессия БД
        
    Returns:
        Dict: Данные пользователя
        
    Raises:
        AuthenticationException: Если токен невалиден
    """
    credentials_exception = AuthenticationException("Неверные учетные данные")

    try:
        payload = await decode_token(token)

        if payload is None:
            raise credentials_exception

        nickname: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("user_id")

        if nickname is None or user_id is None:
            raise credentials_exception

        return {"nickname": nickname, "user_id": user_id, "token": token}

    except JWTError as e:
        logger.warning(f"JWT ошибка: {e}")
        raise credentials_exception


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """
    Получение текущего пользователя (опционально).
    
    Args:
        request: HTTP запрос
        db: Сессия БД
        
    Returns:
        Optional[Dict]: Данные пользователя или None
    """
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        payload = await decode_token(token)

        if payload is None:
            return None

        nickname = payload.get("sub")
        user_id = payload.get("user_id")

        if nickname is None or user_id is None:
            return None

        return {"nickname": nickname, "user_id": user_id, "token": token}

    except Exception:
        return None


def get_client_ip(request: Request) -> str:
    """
    Получение IP адреса клиента.
    
    Args:
        request: HTTP запрос
        
    Returns:
        str: IP адрес
    """
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"