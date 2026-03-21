#!/usr/bin/env python3
"""
=============================================================================
APP API AUTH
API эндпоинты авторизации и аутентификации
=============================================================================
"""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, get_current_user, get_client_ip
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    NotFoundException,
    AccountLockedException,
)
from app.db.session import AsyncSession
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailRequest,
    ResendCodeRequest,
    AuthResponse,
    UserProfileResponse,
    ChangePasswordRequest,
    SessionResponse,
    SessionsListResponse,
)
from app.services.auth import AuthService
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Роутер
router = APIRouter(prefix="/auth", tags=["Авторизация"])


# =============================================================================
# РЕГИСТРАЦИЯ
# =============================================================================
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
        request: Request,
        data: RegisterRequest,
        db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Регистрация нового пользователя.
    
    - **nickname**: Никнейм (3-50 символов)
    - **email**: Email адрес (обязательно)
    - **password**: Пароль (мин. 8 символов)
    """
    client_ip = get_client_ip(request)
    logger.info(f"📝 Новая регистрация: nickname={data.nickname}")

    auth_service = AuthService(db)

    try:
        user, access_token = await auth_service.register_user(
            nickname=data.nickname,
            email=data.email,
            password=data.password,
            ip_address=client_ip,
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            nickname=user.nickname,
            email_verified=user.email_verified,
            message="Пользователь успешно зарегистрирован",
        )

    except ValidationException as e:
        logger.warning(f"⚠️ Ошибка валидации при регистрации: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации: {e}")
        raise ValidationException("Ошибка при регистрации")


# =============================================================================
# ВХОД
# =============================================================================
@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(
        request: Request,
        data: LoginRequest,
        db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Вход пользователя в систему.
    
    - **username**: Никнейм или email
    - **password**: Пароль
    """
    client_ip = get_client_ip(request)
    logger.info(f"🔑 Вход: username={data.username}")

    auth_service = AuthService(db)

    try:
        result = await auth_service.login_user(
            username=data.username,
            password=data.password,
            ip_address=client_ip,
        )

        return AuthResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user_id=result["user_id"],
            nickname=result["nickname"],
            email_verified=result["email_verified"],
            message="Вход выполнен успешно",
        )

    except (AuthenticationException, AccountLockedException) as e:
        logger.warning(f"⚠️ Ошибка входа: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при входе: {e}")
        raise AuthenticationException("Ошибка при входе")


# =============================================================================
# ПОДТВЕРЖДЕНИЕ EMAIL
# =============================================================================
@router.post("/verify-email", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def verify_email(
        request: Request,
        data: VerifyEmailRequest,
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Подтверждение email адреса.
    
    - **user_id**: ID пользователя
    - **code**: 6-значный код из письма
    """
    auth_service = AuthService(db)

    try:
        await auth_service.verify_email(
            user_id=data.user_id,
            code=data.code,
        )

        return {"message": "Email успешно подтверждён", "email_verified": True}

    except ValidationException as e:
        logger.warning(f"⚠️ Ошибка подтверждения email: {e.detail}")
        raise
    except NotFoundException as e:
        logger.warning(f"⚠️ Пользователь не найден: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при подтверждении email: {e}")
        raise ValidationException("Ошибка при подтверждении email")


# =============================================================================
# ПОВТОРНАЯ ОТПРАВКА КОДА
# =============================================================================
@router.post("/resend-code", response_model=Dict[str, Any])
@limiter.limit("3/minute")
async def resend_verification_code(
        request: Request,
        data: ResendCodeRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Отправить код подтверждения email повторно.
    """
    client_ip = get_client_ip(request)
    logger.info(f"📬 Запрос на повторную отправку кода: user_id={current_user['user_id']}")

    auth_service = AuthService(db)

    try:
        email = await auth_service.resend_verification_code(
            user_id=current_user["user_id"],
            client_ip=client_ip,
        )

        return {"message": "Код отправлен на вашу почту", "email": email}

    except ValidationException as e:
        logger.warning(f"⚠️ Ошибка отправки кода: {e.detail}")
        raise
    except NotFoundException as e:
        logger.warning(f"⚠️ Пользователь не найден: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке кода: {e}")
        raise ValidationException("Ошибка при отправке кода")


# =============================================================================
# ВЫХОД
# =============================================================================
@router.post("/logout", response_model=Dict[str, Any])
async def logout(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Выход пользователя из системы.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.logout(user_id=current_user["user_id"])
        return {"message": "Выход выполнен успешно"}

    except Exception as e:
        logger.error(f"❌ Ошибка при выходе: {e}")
        raise ValidationException("Ошибка при выходе")


# =============================================================================
# ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
# =============================================================================
@router.get("/me", response_model=UserProfileResponse)
async def get_me(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Получение информации о текущем пользователе.
    """
    auth_service = AuthService(db)

    try:
        profile = await auth_service.get_user_profile(user_id=current_user["user_id"])

        return UserProfileResponse(
            user_id=profile["user_id"],
            nickname=profile["nickname"],
            email=profile["email"],
            email_verified=profile["email_verified"],
            created_at=profile["created_at"],
            last_login=profile["last_login"],
        )

    except NotFoundException as e:
        logger.warning(f"⚠️ Пользователь не найден: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении профиля: {e}")
        raise NotFoundException("Пользователь не найден")


# =============================================================================
# СМЕНА ПАРОЛЯ
# =============================================================================
@router.post("/change-password", response_model=Dict[str, Any])
@limiter.limit("3/minute")
async def change_password(
        request: Request,
        data: ChangePasswordRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Изменение пароля пользователя.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.change_password(
            user_id=current_user["user_id"],
            current_password=data.current_password,
            new_password=data.new_password,
        )

        return {"message": "Пароль успешно изменён"}

    except (AuthenticationException, ValidationException) as e:
        logger.warning(f"⚠️ Ошибка смены пароля: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при смене пароля: {e}")
        raise ValidationException("Ошибка при смене пароля")


# =============================================================================
# СЕССИИ
# =============================================================================
@router.get("/sessions", response_model=SessionsListResponse)
async def get_sessions(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> SessionsListResponse:
    """
    Получить список активных сессий.
    """
    auth_service = AuthService(db)

    try:
        sessions = await auth_service.get_sessions(user_id=current_user["user_id"])
        return SessionsListResponse(sessions=sessions)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении сессий: {e}")
        return SessionsListResponse(sessions=[])


@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def terminate_session(
        session_id: int,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Завершить конкретную сессию.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.terminate_session(
            user_id=current_user["user_id"],
            session_id=session_id,
        )

        return {"message": "Сессия завершена"}

    except NotFoundException as e:
        logger.warning(f"⚠️ Сессия не найдена: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении сессии: {e}")
        raise ValidationException("Ошибка при завершении сессии")


@router.delete("/sessions", response_model=Dict[str, Any])
async def terminate_all_sessions(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Завершить все сессии кроме текущей.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.terminate_all_sessions(user_id=current_user["user_id"])
        return {"message": "Все сессии завершены"}

    except Exception as e:
        logger.error(f"❌ Ошибка при завершении сессий: {e}")
        raise ValidationException("Ошибка при завершении сессий")


# =============================================================================
# УДАЛЕНИЕ АККАУНТА
# =============================================================================
@router.delete("/delete-account", response_model=Dict[str, Any])
async def delete_account(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Удалить аккаунт пользователя.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.delete_account(user_id=current_user["user_id"])
        return {"message": "Аккаунт успешно удалён"}

    except NotFoundException as e:
        logger.warning(f"⚠️ Пользователь не найден: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении аккаунта: {e}")
        raise ValidationException("Ошибка при удалении аккаунта")