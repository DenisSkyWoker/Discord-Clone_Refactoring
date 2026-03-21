#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS AUTH
Pydantic схемы для авторизации и аутентификации
=============================================================================
"""
import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.validators import validate_password_strength


# =============================================================================
# ЗАПРОСЫ
# =============================================================================
class RegisterRequest(BaseModel):
    """
    Схема запроса регистрации пользователя.
    
    Attributes:
        nickname: Никнейм пользователя (3-50 символов)
        email: Email адрес (обязательно)
        password: Пароль (мин. 8 символов, заглавные, строчные, цифры)
    """
    nickname: str = Field(..., min_length=3, max_length=50, description="Никнейм пользователя")
    email: EmailStr = Field(..., description="Email адрес")
    password: str = Field(..., min_length=8, description="Пароль")

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        """Валидация никнейма."""
        if not re.match(r"^[a-zA-Zа-яА-Я0-9_]+$", v):
            raise ValueError("Никнейм может содержать только буквы, цифры и подчёркивание")
        if v.lower() in ["admin", "mod", "administrator", "модератор", "админ"]:
            raise ValueError("Этот никнейм зарезервирован")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Валидация email."""
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация сложности пароля."""
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


class LoginRequest(BaseModel):
    """
    Схема запроса входа в систему.
    
    Attributes:
        username: Никнейм или email
        password: Пароль
    """
    username: str = Field(..., min_length=1, max_length=50, description="Никнейм или email")
    password: str = Field(..., min_length=1, description="Пароль")


class VerifyEmailRequest(BaseModel):
    """
    Схема запроса подтверждения email.
    
    Attributes:
        user_id: ID пользователя
        code: 6-значный код подтверждения
    """
    user_id: int = Field(..., gt=0, description="ID пользователя")
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Код подтверждения")


class ResendCodeRequest(BaseModel):
    """
    Схема запроса повторной отправки кода подтверждения.
    
    Attributes:
        user_id: ID пользователя
    """
    user_id: int = Field(..., gt=0, description="ID пользователя")


class ChangePasswordRequest(BaseModel):
    """
    Схема запроса смены пароля.
    
    Attributes:
        current_password: Текущий пароль
        new_password: Новый пароль
    """
    current_password: str = Field(..., min_length=1, description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Валидация сложности нового пароля."""
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


# =============================================================================
# ОТВЕТЫ
# =============================================================================
class AuthResponse(BaseModel):
    """
    Схема ответа авторизации.
    
    Attributes:
        access_token: JWT токен доступа
        token_type: Тип токена (bearer)
        user_id: ID пользователя
        nickname: Никнейм пользователя
        email_verified: Статус подтверждения email
        message: Сообщение (опционально)
    """
    access_token: Optional[str] = Field(None, description="JWT токен доступа")
    token_type: str = Field("bearer", description="Тип токена")
    user_id: int = Field(..., description="ID пользователя")
    nickname: str = Field(..., description="Никнейм пользователя")
    email_verified: bool = Field(False, description="Статус подтверждения email")
    message: Optional[str] = Field(None, description="Сообщение")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "nickname": "User123",
                "email_verified": False,
                "message": "Вход выполнен успешно"
            }
        }
    }


class TokenResponse(BaseModel):
    """
    Схема ответа с токеном.
    
    Attributes:
        access_token: JWT токен доступа
        token_type: Тип токена
    """
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("bearer", description="Тип токена")


class UserProfileResponse(BaseModel):
    """
    Схема ответа с данными профиля пользователя.
    
    Attributes:
        user_id: ID пользователя
        nickname: Никнейм
        email: Email адрес
        email_verified: Статус подтверждения email
        created_at: Дата регистрации
        last_login: Последний вход
    """
    user_id: int = Field(..., description="ID пользователя")
    nickname: str = Field(..., description="Никнейм")
    email: Optional[str] = Field(None, description="Email адрес")
    email_verified: bool = Field(False, description="Статус подтверждения email")
    created_at: Optional[datetime] = Field(None, description="Дата регистрации")
    last_login: Optional[datetime] = Field(None, description="Последний вход")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "nickname": "User123",
                "email": "user@example.com",
                "email_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-15T12:30:00"
            }
        }
    }


class SessionResponse(BaseModel):
    """
    Схема ответа с информацией о сессии.
    
    Attributes:
        id: ID сессии
        device: Устройство
        ip_address: IP адрес
        last_active: Последняя активность
        is_current: Текущая сессия
    """
    id: int = Field(..., description="ID сессии")
    device: str = Field("Веб-браузер", description="Устройство")
    ip_address: str = Field(..., description="IP адрес")
    last_active: str = Field(..., description="Последняя активность")
    is_current: bool = Field(False, description="Текущая сессия")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "device": "Веб-браузер",
                "ip_address": "192.168.1.1",
                "last_active": "15.01.2024 12:30",
                "is_current": True
            }
        }
    }


class SessionsListResponse(BaseModel):
    """
    Схема ответа со списком сессий.
    
    Attributes:
        sessions: Список сессий
    """
    sessions: List[SessionResponse] = Field(..., description="Список сессий")