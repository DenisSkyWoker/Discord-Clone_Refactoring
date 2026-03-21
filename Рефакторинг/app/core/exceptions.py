#!/usr/bin/env python3
"""
Кастомные исключения приложения
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Базовое исключение приложения."""

    def __init__(
            self,
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
            message: str = "Внутренняя ошибка сервера",
            details: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"message": message, "details": details or {}},
            headers=headers,
        )


class AuthenticationException(AppException):
    """Ошибка аутентификации."""

    def __init__(self, message: str = "Неверные учетные данные"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(AppException):
    """Ошибка авторизации."""

    def __init__(self, message: str = "Недостаточно прав"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
        )


class NotFoundException(AppException):
    """Ресурс не найден."""

    def __init__(self, message: str = "Ресурс не найден"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
        )


class ValidationException(AppException):
    """Ошибка валидации данных."""

    def __init__(self, message: str = "Неверные данные"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
        )


class DatabaseException(AppException):
    """Ошибка базы данных."""

    def __init__(self, message: str = "Ошибка базы данных"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
        )


class RateLimitException(AppException):
    """Превышен лимит запросов."""

    def __init__(self, message: str = "Слишком много запросов"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
        )


class AccountLockedException(AppException):
    """Аккаунт заблокирован."""

    def __init__(self, message: str = "Аккаунт заблокирован"):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            message=message,
        )