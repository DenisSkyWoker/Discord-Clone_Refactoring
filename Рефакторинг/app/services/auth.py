#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES AUTH
Сервис авторизации и аутентификации
=============================================================================
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_secure_token,
    generate_verification_code,
    decode_token,
)
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
    AccountLockedException,
)
from app.db.models import (
    RegisteredUser,
    EmailVerificationCode,
    ConnectedUser,
    SecurityLog,
    Message,
    Channel,
)
from app.utils.helpers import to_db_datetime, validate_password_strength
from app.utils.logging import get_logger
from app.utils.security_logger import log_security_event
from app.services.email import send_verification_email

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """Сервис для операций авторизации и аутентификации."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(
            self,
            nickname: str,
            email: str,
            password: str,
            ip_address: str,
    ) -> Tuple[RegisteredUser, str]:
        """
        Регистрация нового пользователя.
        
        Args:
            nickname: Никнейм
            email: Email
            password: Пароль
            ip_address: IP адрес
            
        Returns:
            Tuple[RegisteredUser, str]: Пользователь и токен доступа
            
        Raises:
            ValidationException: Если данные невалидны
        """
        # Проверка существующего пользователя
        result = await self.session.execute(
            select(RegisteredUser).where(RegisteredUser.nickname == nickname)
        )
        if result.scalar_one_or_none():
            log_security_event("REGISTRATION_ATTEMPT", {
                "ip": ip_address,
                "nickname": nickname,
                "status": "duplicate_nickname",
            })
            raise ValidationException("Пользователь с таким ником уже существует")

        # Проверка существующего email
        result = await self.session.execute(
            select(RegisteredUser).where(RegisteredUser.email == email)
        )
        if result.scalar_one_or_none():
            log_security_event("REGISTRATION_ATTEMPT", {
                "ip": ip_address,
                "email": email,
                "status": "duplicate_email",
            })
            raise ValidationException("Этот email уже зарегистрирован")

        # Создание пользователя
        new_user = RegisteredUser(
            nickname=nickname,
            email=email,
            password_hash=get_password_hash(password),
            email_verified=False,
            last_ip=ip_address,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        # Создание токена
        access_token = create_access_token(
            data={"sub": new_user.nickname, "user_id": new_user.id},
        )

        log_security_event("USER_REGISTERED", {
            "user_id": new_user.id,
            "nickname": new_user.nickname,
            "ip": ip_address,
        })

        return new_user, access_token

    async def login_user(
            self,
            username: str,
            password: str,
            ip_address: str,
    ) -> Dict[str, Any]:
        """
        Вход пользователя в систему.
        
        Args:
            username: Никнейм или email
            password: Пароль
            ip_address: IP адрес
            
        Returns:
            Dict: Данные для ответа
            
        Raises:
            AuthenticationException: Если credentials неверны
            AccountLockedException: Если аккаунт заблокирован
        """
        result = await self.session.execute(
            select(RegisteredUser).where(RegisteredUser.nickname == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            log_security_event("LOGIN_FAILED", {
                "ip": ip_address,
                "nickname": username,
                "reason": "user_not_found",
            })
            raise AuthenticationException("Неверный логин или пароль")

        # Проверка блокировки
        if user.locked_until and user.locked_until > to_db_datetime(datetime.now(timezone.utc)):
            lockout_remaining = int((
                                            user.locked_until - to_db_datetime(datetime.now(timezone.utc))
                                    ).total_seconds() / 60)

            log_security_event("LOGIN_BLOCKED", {
                "user_id": user.id,
                "ip": ip_address,
                "lockout_minutes": lockout_remaining,
            })
            raise AccountLockedException(f"Аккаунт заблокирован. Попробуйте через {lockout_remaining} мин.")

        # Проверка пароля
        if not verify_password(password, str(user.password_hash)):
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.LOGIN_LOCKOUT_MINUTES
                )
                user.failed_login_attempts = 0

                log_security_event("ACCOUNT_LOCKED", {
                    "user_id": user.id,
                    "ip": ip_address,
                })
                logger.warning(f"🔒 Аккаунт {user.nickname} заблокирован на {settings.LOGIN_LOCKOUT_MINUTES} мин.")

            await self.session.commit()

            log_security_event("LOGIN_FAILED", {
                "user_id": user.id,
                "ip": ip_address,
                "attempts": user.failed_login_attempts,
            })
            raise AuthenticationException("Неверный логин или пароль")

        # Успешный вход
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = to_db_datetime(datetime.now(timezone.utc))
        user.last_ip = ip_address
        user.session_token = generate_secure_token()

        await self.session.commit()

        access_token = create_access_token(
            data={"sub": user.nickname, "user_id": user.id, "jti": user.session_token},
        )

        log_security_event("LOGIN_SUCCESS", {
            "user_id": user.id,
            "nickname": user.nickname,
            "ip": ip_address,
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "nickname": user.nickname,
            "email_verified": user.email_verified if user.email_verified is not None else True,
        }

    async def verify_email(self, user_id: int, code: str) -> bool:
        """
        Подтверждение email адреса.
        
        Args:
            user_id: ID пользователя
            code: Код подтверждения
            
        Returns:
            bool: True если успешно
            
        Raises:
            ValidationException: Если код неверный
            NotFoundException: Если пользователь не найден
        """
        result = await self.session.execute(
            select(EmailVerificationCode)
            .where(EmailVerificationCode.user_id == user_id)
            .where(EmailVerificationCode.code == code)
            .where(EmailVerificationCode.is_used == False)
            .where(EmailVerificationCode.expires_at > to_db_datetime(datetime.now(timezone.utc)))
            .order_by(EmailVerificationCode.created_at.desc())
        )
        verification = result.scalar_one_or_none()

        if not verification:
            log_security_event("VERIFY_FAILED", {"user_id": user_id})
            raise ValidationException("Неверный или истёкший код подтверждения")

        user_result = await self.session.execute(
            select(RegisteredUser).where(RegisteredUser.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundException("Пользователь не найден")

        user.email_verified = True
        verification.is_used = True

        await self.session.commit()

        log_security_event("EMAIL_VERIFIED", {"user_id": user.id})
        logger.info(f"✅ Email подтверждён для пользователя: {user.nickname} (ID: {user.id})")

        return True

    async def resend_verification_code(self, user_id: int, client_ip: str) -> str:
        """
        Отправить код подтверждения email повторно.
        
        Args:
            user_id: ID пользователя
            client_ip: IP адрес
            
        Returns:
            str: Email адрес
            
        Raises:
            NotFoundException: Если пользователь не найден
            ValidationException: Если email не указан или уже подтверждён
        """
        user = await self.session.get(RegisteredUser, user_id)

        if not user:
            raise NotFoundException("Пользователь не найден")

        if not user.email:
            raise ValidationException("Email не указан")

        if user.email_verified:
            raise ValidationException("Email уже подтверждён")

        # Деактивация старых кодов
        await self.session.execute(
            text("""
                 UPDATE email_verification_codes
                 SET is_used = TRUE
                 WHERE user_id = :user_id AND is_used = FALSE
                 """),
            {"user_id": user.id},
        )

        # Генерация нового кода
        code = generate_verification_code()
        expires_at = to_db_datetime(
            datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        )

        verification_code = EmailVerificationCode(
            user_id=user.id,
            code=code,
            email=user.email,
            expires_at=expires_at,
        )
        self.session.add(verification_code)
        await self.session.commit()

        # Отправка email
        email_sent = await send_verification_email(user.email, code, user.nickname)

        if not email_sent:
            raise Exception("Не удалось отправить email")

        log_security_event("VERIFICATION_CODE_RESENT", {
            "user_id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "ip": client_ip,
        })

        return user.email

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Получение профиля пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Данные профиля
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        result = await self.session.execute(
            select(RegisteredUser).where(RegisteredUser.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("Пользователь не найден")

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    async def update_profile(
            self,
            user_id: int,
            nickname: Optional[str] = None,
            email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Обновление профиля пользователя.
        
        Args:
            user_id: ID пользователя
            nickname: Новый никнейм
            email: Новый email
            
        Returns:
            Dict: Обновлённые данные
            
        Raises:
            NotFoundException: Если пользователь не найден
            ValidationException: Если данные невалидны
        """
        user = await self.session.get(RegisteredUser, user_id)

        if not user:
            raise NotFoundException("Пользователь не найден")

        email_verification_sent = False

        if nickname and nickname != user.nickname:
            # Проверка занятости никнейма
            result = await self.session.execute(
                select(RegisteredUser).where(RegisteredUser.nickname == nickname)
            )
            if result.scalar_one_or_none():
                raise ValidationException("Никнейм уже занят")
            user.nickname = nickname

        if email and email != user.email:
            user.email = email
            user.email_verified = False

            # Генерация кода подтверждения
            code = generate_verification_code()
            expires_at = to_db_datetime(
                datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
            )

            verification_code = EmailVerificationCode(
                user_id=user.id,
                code=code,
                email=email,
                expires_at=expires_at,
            )
            self.session.add(verification_code)

            email_sent = await send_verification_email(email, code, user.nickname)
            if email_sent:
                email_verification_sent = True

        await self.session.commit()

        log_security_event("PROFILE_UPDATED", {
            "user_id": user.id,
            "nickname": user.nickname,
            "email": email,
        })

        return {
            "message": "Профиль обновлён",
            "nickname": user.nickname,
            "email": user.email,
            "email_verification_sent": email_verification_sent,
        }

    async def change_password(
            self,
            user_id: int,
            current_password: str,
            new_password: str,
    ) -> bool:
        """
        Изменение пароля пользователя.
        
        Args:
            user_id: ID пользователя
            current_password: Текущий пароль
            new_password: Новый пароль
            
        Returns:
            bool: True если успешно
            
        Raises:
            AuthenticationException: Если текущий пароль неверен
            ValidationException: Если новый пароль не соответствует требованиям
        """
        user = await self.session.get(RegisteredUser, user_id)

        if not user:
            raise NotFoundException("Пользователь не найден")

        if not verify_password(current_password, str(user.password_hash)):
            log_security_event("PASSWORD_CHANGE_FAILED", {
                "user_id": user.id,
                "reason": "wrong_current_password",
            })
            raise AuthenticationException("Неверный текущий пароль")

        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            raise ValidationException(message)

        user.password_hash = get_password_hash(new_password)
        user.session_token = generate_secure_token()

        await self.session.commit()

        log_security_event("PASSWORD_CHANGED", {"user_id": user.id})
        logger.info(f"✅ Пароль изменён для пользователя: {user.nickname} (ID: {user.id})")

        return True

    async def get_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка активных сессий.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Dict]: Список сессий
        """
        result = await self.session.execute(
            select(ConnectedUser)
            .where(ConnectedUser.user_id == user_id)
            .where(ConnectedUser.is_online == True)
            .order_by(ConnectedUser.connected_at.desc())
        )
        sessions = result.scalars().all()

        session_list = []
        for i, s in enumerate(sessions):
            session_list.append({
                "id": s.id,
                "device": "Веб-браузер",
                "ip_address": s.ip_address,
                "last_active": s.connected_at.strftime("%d.%m.%Y %H:%M") if s.connected_at else "Неизвестно",
                "is_current": i == 0,
            })

        return session_list

    async def terminate_session(self, user_id: int, session_id: int) -> bool:
        """
        Завершение конкретной сессии.
        
        Args:
            user_id: ID пользователя
            session_id: ID сессии
            
        Returns:
            bool: True если успешно
        """
        session_obj = await self.session.get(ConnectedUser, session_id)

        if not session_obj or session_obj.user_id != user_id:
            raise NotFoundException("Сессия не найдена")

        session_obj.is_online = False
        await self.session.commit()

        log_security_event("SESSION_TERMINATED", {
            "user_id": user_id,
            "session_id": session_id,
        })

        return True

    async def terminate_all_sessions(self, user_id: int) -> bool:
        """
        Завершение всех сессий кроме текущей.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно
        """
        await self.session.execute(
            text("""
                 UPDATE connected_users
                 SET is_online = FALSE
                 WHERE user_id = :user_id AND is_online = TRUE
                 """),
            {"user_id": user_id},
        )
        await self.session.commit()

        log_security_event("ALL_SESSIONS_TERMINATED", {"user_id": user_id})

        return True

    async def delete_account(self, user_id: int) -> bool:
        """
        Удаление аккаунта пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно
        """
        user = await self.session.get(RegisteredUser, user_id)

        if not user:
            raise NotFoundException("Пользователь не найден")

        nickname = user.nickname

        # Удаление связанных данных
        await self.session.execute(delete(Message).where(Message.user_id == user.id))
        await self.session.execute(delete(Channel).where(Channel.creator_id == user.id))
        await self.session.execute(delete(ConnectedUser).where(ConnectedUser.user_id == user.id))
        await self.session.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user.id))

        await self.session.delete(user)
        await self.session.commit()

        log_security_event("ACCOUNT_DELETED", {
            "user_id": user.id,
            "nickname": nickname,
        })
        logger.warning(f"🗑️ Аккаунт удалён: {nickname} (ID: {user.id})")

        return True

    async def logout(self, user_id: int) -> bool:
        """
        Выход пользователя из системы.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно
        """
        user = await self.session.get(RegisteredUser, user_id)

        if user:
            user.session_token = None
            await self.session.commit()

        log_security_event("LOGOUT", {"user_id": user_id})

        return True