#!/usr/bin/env python3
"""
=============================================================================
APP API WEBSOCKET
WebSocket эндпоинты для чата
=============================================================================
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select, text

from app.core.config import get_settings
from app.db.models import (
    Message,
    MessageStatus,
    MessageAttachment,
    RegisteredUser,
    ConnectedUser,
)
from app.db.session import async_session_maker
from app.services.websocket_manager import manager
from app.utils.helpers import sanitize_input, to_db_datetime
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Роутер
router = APIRouter(tags=["WebSocket"])


# =============================================================================
# WEBSOCKET ПОДКЛЮЧЕНИЕ
# =============================================================================
@router.websocket("/ws/{channel}/{nickname}/{token}")
async def websocket_endpoint(
        websocket: WebSocket,
        channel: str,
        nickname: str,
        token: str,
) -> None:
    """
    Обработка WebSocket подключений для чата.
    
    Args:
        websocket: WebSocket соединение
        channel: Название канала
        nickname: Никнейм пользователя
        token: JWT токен авторизации
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else 0
    current_channel: str = channel
    user_id: Optional[int] = None
    token_nickname: Optional[str] = None

    # =========================================================================
    # ПРОВЕРКА ТОКЕНА
    # =========================================================================
    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("user_id")
        token_nickname = payload.get("sub")

        if not user_id or not token_nickname or token_nickname != nickname:
            logger.warning(f"⚠️ Неверный токен для {nickname}")
            await websocket.close(code=4003, reason="Invalid token")
            return

    except JWTError as e:
        logger.warning(f"⚠️ JWT ошибка для {nickname}: {e}")
        await websocket.close(code=4003, reason="Invalid token")
        return

    logger.info(f"🔌 Подключение: {nickname} (ID: {user_id}) к каналу {channel} ({client_host}:{client_port})")

    # Подключение к менеджеру
    await manager.connect(websocket, nickname, channel, user_id)

    try:
        async with async_session_maker() as session:
            # Регистрация сессии
            new_user = ConnectedUser(
                user_id=user_id,
                nickname=nickname,
                ip_address=client_host,
                port=client_port,
                current_channel=channel,
            )
            session.add(new_user)
            await session.commit()

            # Приветственное сообщение
            await websocket.send_json({
                "type": "system",
                "content": f"Добро пожаловать, {nickname}!",
                "channel": channel,
            })

            # =========================================================================
            # ОТПРАВКА ИСТОРИИ СООБЩЕНИЙ
            # =========================================================================
            result = await session.execute(
                select(Message)
                .where(Message.channel == channel)
                .order_by(Message.created_at.desc())
                .limit(50)
            )
            messages = result.scalars().all()

            # Получаем статусы для всех сообщений
            message_ids = [m.id for m in messages]

            if message_ids:
                status_result = await session.execute(
                    select(MessageStatus).where(
                        MessageStatus.message_id.in_(message_ids),
                        MessageStatus.user_id == user_id,
                        )
                )
                statuses = {s.message_id: s for s in status_result.scalars()}
            else:
                statuses = {}

            # Формируем ответ
            messages_data = []
            for m in reversed(messages):
                status = "read"
                if m.user_id == user_id:
                    msg_status = statuses.get(m.id)
                    if msg_status and msg_status.is_read:
                        status = "read"
                    elif msg_status and msg_status.is_delivered:
                        status = "delivered"
                    else:
                        status = "sent"

                messages_data.append({
                    "id": m.id,
                    "nickname": sanitize_input(m.nickname),
                    "content": sanitize_input(m.content),
                    "time": m.created_at.isoformat(),
                    "sender_id": m.user_id,
                    "status": status,
                    "attachments": [
                        {
                            "file_name": att.file_name,
                            "file_url": f"/api/files/{att.file_path}",
                            "file_size": att.file_size,
                            "file_type": att.file_type,
                            "width": att.width,
                            "height": att.height,
                            "duration": att.duration,
                        }
                        for att in m.attachments
                    ] if m.attachments else [],
                })

            await websocket.send_json({
                "type": "message_history",
                "messages": messages_data,
            })

            # Отмечаем сообщения как доставленные
            for msg in messages:
                if msg.user_id != user_id:
                    try:
                        await session.execute(
                            text("""
                                 INSERT INTO message_statuses (message_id, user_id, is_delivered, delivered_at)
                                 VALUES (:message_id, :user_id, TRUE, NOW())
                                     ON CONFLICT (message_id, user_id)
                                DO UPDATE SET is_delivered = TRUE, delivered_at = NOW()
                                 """),
                            {"message_id": msg.id, "user_id": user_id},
                        )

                        author_result = await session.execute(
                            select(RegisteredUser.nickname).where(RegisteredUser.id == msg.user_id)
                        )
                        author_nickname = author_result.scalar_one_or_none()

                        if author_nickname and author_nickname != nickname:
                            await manager.send_to_user(
                                author_nickname,
                                {
                                    "type": "message_status_update",
                                    "message_id": msg.id,
                                    "status": "delivered",
                                },
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обновления статуса доставки: {e}")

            await session.commit()

            # Уведомление о подключении
            await manager.send_to_channel(
                channel,
                {
                    "type": "system",
                    "content": f"{nickname} зашёл в чат",
                    "channel": channel,
                },
            )

            await manager.broadcast_online_users(channel)

    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА при подключении {nickname}: {e}")
        await manager.disconnect(websocket)
        return

    logger.info(f"✅ {nickname} успешно подключён, ожидание сообщений...")

    # =========================================================================
    # ОБРАБОТКА СООБЩЕНИЙ
    # =========================================================================
    try:
        while True:
            data = await websocket.receive_json()

            # -----------------------------------------------------------------
            # ПРОЧТЕНИЕ СООБЩЕНИЙ
            # -----------------------------------------------------------------
            if data.get("type") == "message_read":
                message_ids = data.get("message_ids", [])

                try:
                    async with async_session_maker() as session:
                        for msg_id in message_ids:
                            try:
                                await session.execute(
                                    text("""
                                         INSERT INTO message_statuses (message_id, user_id, is_read, read_at)
                                         VALUES (:message_id, :user_id, TRUE, NOW())
                                             ON CONFLICT (message_id, user_id)
                                        DO UPDATE SET is_read = TRUE, read_at = NOW()
                                         """),
                                    {"message_id": msg_id, "user_id": user_id},
                                )

                                msg_result = await session.execute(
                                    select(Message).where(Message.id == msg_id)
                                )
                                msg = msg_result.scalar_one_or_none()

                                if msg and msg.user_id != user_id:
                                    author_result = await session.execute(
                                        select(RegisteredUser.nickname).where(RegisteredUser.id == msg.user_id)
                                    )
                                    author_nickname = author_result.scalar_one_or_none()

                                    if author_nickname:
                                        await manager.send_to_user(
                                            author_nickname,
                                            {
                                                "type": "message_status_update",
                                                "message_id": msg_id,
                                                "status": "read",
                                            },
                                        )
                            except Exception as e:
                                logger.warning(f"⚠️ Ошибка обновления статуса прочтения: {e}")

                        await session.commit()
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки message_read: {e}")

                continue

            # -----------------------------------------------------------------
            # ПЕРЕКЛЮЧЕНИЕ КАНАЛА
            # -----------------------------------------------------------------
            if data.get("type") == "switch_channel":
                new_channel = data.get("channel", "общий-чат")

                if await manager.switch_channel(websocket, new_channel):
                    current_channel = new_channel

                    try:
                        async with async_session_maker() as session:
                            result = await session.execute(
                                select(Message)
                                .where(Message.channel == new_channel)
                                .order_by(Message.created_at.desc())
                                .limit(50)
                            )
                            messages = result.scalars().all()

                            message_ids = [m.id for m in messages]

                            if message_ids:
                                status_result = await session.execute(
                                    select(MessageStatus).where(
                                        MessageStatus.message_id.in_(message_ids),
                                        MessageStatus.user_id == user_id,
                                        )
                                )
                                statuses = {s.message_id: s for s in status_result.scalars()}
                            else:
                                statuses = {}

                            messages_data = []
                            for m in reversed(messages):
                                status = "read"
                                if m.user_id == user_id:
                                    msg_status = statuses.get(m.id)
                                    if msg_status and msg_status.is_read:
                                        status = "read"
                                    elif msg_status and msg_status.is_delivered:
                                        status = "delivered"
                                    else:
                                        status = "sent"

                                messages_data.append({
                                    "id": m.id,
                                    "nickname": sanitize_input(m.nickname),
                                    "content": sanitize_input(m.content),
                                    "time": m.created_at.isoformat(),
                                    "sender_id": m.user_id,
                                    "status": status,
                                })

                            await websocket.send_json({
                                "type": "message_history",
                                "messages": messages_data,
                            })

                            await session.commit()

                    except Exception as e:
                        logger.error(f"❌ Ошибка переключения канала: {e}")

                    await websocket.send_json({
                        "type": "channel_switched",
                        "channel": new_channel,
                    })

                    await manager.broadcast_online_users(new_channel)

                continue

            # -----------------------------------------------------------------
            # ОТПРАВКА СООБЩЕНИЯ
            # -----------------------------------------------------------------
            content = data.get("content", "") or ""
            attachments_data = data.get("attachments", [])
            has_attachments = len(attachments_data) > 0

            if content.strip() or has_attachments:
                target_channel = current_channel

                try:
                    async with async_session_maker() as session:
                        msg = Message(
                            user_id=user_id,
                            nickname=nickname,
                            content=sanitize_input(content),
                            channel=target_channel,
                        )
                        session.add(msg)
                        await session.commit()
                        msg_id = msg.id

                        # Сохранение вложений
                        if has_attachments:
                            for att in attachments_data:
                                attachment = MessageAttachment(
                                    message_id=msg_id,
                                    file_name=att.get('file_name', ''),
                                    file_path=att.get('file_url', '').replace('/api/files/', ''),
                                    file_size=att.get('file_size', 0),
                                    file_type=att.get('file_type', ''),
                                    uploaded_at=to_db_datetime(datetime.now(timezone.utc)),
                                    width=att.get('width'),
                                    height=att.get('height'),
                                    duration=att.get('duration'),
                                )
                                session.add(attachment)

                            await session.commit()

                        # Отправка сообщения
                        response_data = {
                            "type": "message",
                            "id": msg_id,
                            "nickname": sanitize_input(nickname),
                            "content": sanitize_input(content),
                            "channel": target_channel,
                            "time": to_db_datetime(datetime.now(timezone.utc)).isoformat(),
                            "sender_id": user_id,
                            "status": "sent",
                            "attachments": attachments_data if has_attachments else [],
                        }

                        await manager.send_to_channel(target_channel, response_data)

                except Exception as msg_error:
                    logger.error(f"💥 Ошибка отправки сообщения: {msg_error}")
            else:
                logger.debug(f"⚪ Пустое сообщение от {nickname} (игнорируется)")

    except WebSocketDisconnect:
        logger.warning(f"👋 Отключение: {nickname} из {current_channel}")

        if current_channel:
            try:
                await manager.send_to_channel(
                    current_channel,
                    {
                        "type": "system",
                        "content": f"{nickname} покинул чат",
                        "channel": current_channel,
                    },
                )
                await manager.broadcast_online_users(current_channel)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отправить уведомление об отключении: {e}")

        await manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"💥 Ошибка сокета {nickname}: {e}")
        await manager.disconnect(websocket)