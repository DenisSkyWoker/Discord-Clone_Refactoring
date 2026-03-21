#!/usr/bin/env python3
"""
Функции безопасности: JWT, пароли, токены
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Ошибка проверки пароля: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Хеширование пароля."""
    return pwd_context.hash(password)


def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
) -> str:
    """Создание JWT токена доступа."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "jti": secrets.token_urlsafe(16),
        "iat": datetime.now(timezone.utc),
    })

    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


async def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодирование JWT токена."""
    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning(f"Ошибка декодирования токена: {e}")
        return None


def generate_secure_token() -> str:
    """Генерация безопасного токена сессии."""
    return secrets.token_urlsafe(32)


def generate_verification_code() -> str:
    """Генерация 6-значного кода верификации."""
    return "".join([str(secrets.randbelow(10)) for _ in range(6)])