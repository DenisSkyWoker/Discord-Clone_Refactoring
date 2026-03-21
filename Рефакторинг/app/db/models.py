#!/usr/bin/env python3
"""
=============================================================================
APP DB MODELS
Модели данных SQLAlchemy для Discord Clone
=============================================================================
"""
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Column,
    UniqueConstraint,
    BigInteger,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship

from app.utils.helpers import to_db_datetime

# =============================================================================
# БАЗОВЫЙ КЛАСС
# =============================================================================
Base = declarative_base()


# =============================================================================
# RegisteredUser - Зарегистрированные пользователи
# =============================================================================
class RegisteredUser(Base):
    """Зарегистрированные пользователи с паролями."""

    __tablename__ = "registered_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    session_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Связи
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_user_nickname', 'nickname'),
        Index('idx_user_email', 'email'),
    )

    def __repr__(self) -> str:
        return f"<RegisteredUser(id={self.id}, nickname='{self.nickname}')>"


# =============================================================================
# EmailVerificationCode - Коды подтверждения email
# =============================================================================
class EmailVerificationCode(Base):
    """Коды подтверждения email."""

    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index('idx_code_user', 'user_id', 'code'),
        Index('idx_code_expires', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f"<EmailVerificationCode(id={self.id}, user_id={self.user_id})>"


# =============================================================================
# PasswordResetToken - Токены сброса пароля
# =============================================================================
class PasswordResetToken(Base):
    """Токены сброса пароля."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("registered_users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Связь с пользователем
    user: Mapped["RegisteredUser"] = relationship("RegisteredUser", back_populates="reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


# =============================================================================
# ConnectedUser - Подключенные пользователи (сессии)
# =============================================================================
class ConnectedUser(Base):
    """Подключенные пользователи (сессии)."""

    __tablename__ = "connected_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    current_channel: Mapped[str] = mapped_column(String(50), default="общий-чат")
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )

    __table_args__ = (
        Index('idx_connected_user', 'user_id', 'is_online'),
        Index('idx_connected_channel', 'current_channel'),
    )

    def __repr__(self) -> str:
        return f"<ConnectedUser(id={self.id}, nickname='{self.nickname}')>"


# =============================================================================
# Message - Сообщения в чате
# =============================================================================
class Message(Base):
    """Сообщения в чате."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="общий-чат", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    edited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связи
    attachments: Mapped[List["MessageAttachment"]] = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_message_channel', 'channel', 'created_at'),
        Index('idx_message_user', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, channel='{self.channel}')>"


# =============================================================================
# MessageStatus - Статусы доставки сообщений
# =============================================================================
class MessageStatus(Base):
    """Статусы доставки сообщений."""

    __tablename__ = "message_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id"), nullable=False)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_user_status"),
        Index('idx_status_message', 'message_id'),
        Index('idx_status_user', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<MessageStatus(id={self.id}, message_id={self.message_id})>"


# =============================================================================
# Channel - Пользовательские каналы
# =============================================================================
class Channel(Base):
    """Пользовательские каналы с паролем."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    creator_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index('idx_channel_name', 'name', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name='{self.name}')>"


# =============================================================================
# SecurityLog - Журнал событий безопасности
# =============================================================================
class SecurityLog(Base):
    """Журнал событий безопасности."""

    __tablename__ = "security_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: to_db_datetime(datetime.now(timezone.utc)),
    )

    __table_args__ = (
        Index('idx_security_log_user', 'user_id', 'created_at'),
        Index('idx_security_log_event', 'event_type', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<SecurityLog(id={self.id}, event_type='{self.event_type}')>"


# =============================================================================
# MessageAttachment - Вложения к сообщениям
# =============================================================================
class MessageAttachment(Base):
    """Вложения к сообщениям (файлы, фото, видео)."""

    __tablename__ = "message_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Связь с сообщением
    message: Mapped["Message"] = relationship("Message", back_populates="attachments")

    __table_args__ = (
        Index('idx_attachment_message', 'message_id'),
    )

    def __repr__(self) -> str:
        return f"<MessageAttachment(id={self.id}, file_name='{self.file_name}')>"