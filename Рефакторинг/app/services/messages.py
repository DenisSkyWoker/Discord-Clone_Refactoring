#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES MESSAGES
Сервис для работы с сообщениями
=============================================================================
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, MessageStatus, RegisteredUser, MessageAttachment
from app.utils.helpers import sanitize_input, to_db_datetime
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MessageService:
    """Сервис для операций с сообщениями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel_messages(
            self,
            channel: str,
            user_id: int,
            limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Получение истории сообщений канала со статусами.
        
        Args:
            channel: Название канала
            user_id: ID пользователя
            limit: Лимит сообщений
            
        Returns:
            List[Dict]: Список сообщений
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.channel == channel)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        # Получаем статусы для всех сообщений
        message_ids = [m.id for m in messages]

        if message_ids:
            status_result = await self.session.execute(
                select(MessageStatus).where(
                    MessageStatus.message_id.in_(message_ids),
                    MessageStatus.user_id == user_id,
                    )
            )
            statuses = {s.message_id: s for s in status_result.scalars()}
        else:
            statuses = {}

        return [
            {
                "id": m.id,
                "nickname": sanitize_input(m.nickname),
                "content": sanitize_input(m.content),
                "time": m.created_at.isoformat() if m.created_at else None,
                "sender_id": m.user_id,
                "channel": m.channel,
                "status": self._get_message_status(m, user_id, statuses),
                "attachments": [
                    {
                        "file_name": att.file_name,
                        "file_url": att.file_path,
                        "file_size": att.file_size,
                        "file_type": att.file_type,
                        "width": att.width,
                        "height": att.height,
                        "duration": att.duration,
                    }
                    for att in m.attachments
                ] if m.attachments else [],
            }
            for m in reversed(messages)
        ]

    def _get_message_status(
            self,
            message: Message,
            user_id: int,
            statuses: Dict[int, MessageStatus],
    ) -> str:
        """
        Определение статуса сообщения.
        
        Args:
            message: Сообщение
            user_id: ID пользователя
            statuses: Словарь статусов
            
        Returns:
            str: Статус (sent, delivered, read)
        """
        if message.user_id != user_id:
            return "read"

        status = statuses.get(message.id)

        if status and status.is_read:
            return "read"
        elif status and status.is_delivered:
            return "delivered"
        else:
            return "sent"

    async def mark_messages_delivered(
            self,
            message_ids: List[int],
            user_id: int,
    ) -> None:
        """
        Отметка сообщений как доставленные.
        
        Args:
            message_ids: Список ID сообщений
            user_id: ID пользователя
        """
        for msg_id in message_ids:
            await self.session.execute(
                text("""
                     INSERT INTO message_statuses (message_id, user_id, is_delivered, delivered_at)
                     VALUES (:message_id, :user_id, TRUE, NOW())
                         ON CONFLICT (message_id, user_id)
                    DO UPDATE SET is_delivered = TRUE, delivered_at = NOW()
                     """),
                {"message_id": msg_id, "user_id": user_id},
            )

        await self.session.commit()

    async def mark_messages_read(
            self,
            message_ids: List[int],
            user_id: int,
    ) -> None:
        """
        Отметка сообщений как прочитанные.
        
        Args:
            message_ids: Список ID сообщений
            user_id: ID пользователя
        """
        for msg_id in message_ids:
            await self.session.execute(
                text("""
                     INSERT INTO message_statuses (message_id, user_id, is_read, read_at)
                     VALUES (:message_id, :user_id, TRUE, NOW())
                         ON CONFLICT (message_id, user_id)
                    DO UPDATE SET is_read = TRUE, read_at = NOW()
                     """),
                {"message_id": msg_id, "user_id": user_id},
            )

        await self.session.commit()

    async def create_message(
            self,
            user_id: int,
            nickname: str,
            content: str,
            channel: str,
            attachments: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Создание нового сообщения.
        
        Args:
            user_id: ID пользователя
            nickname: Никнейм
            content: Текст сообщения
            channel: Канал
            attachments: Вложения
            
        Returns:
            Dict: Данные сообщения
        """
        msg = Message(
            user_id=user_id,
            nickname=nickname,
            content=sanitize_input(content),
            channel=channel,
        )
        self.session.add(msg)
        await self.session.commit()

        # Сохранение вложений
        if attachments:
            for att in attachments:
                attachment = MessageAttachment(
                    message_id=msg.id,
                    file_name=att.get('file_name', ''),
                    file_path=att.get('file_url', ''),
                    file_size=att.get('file_size', 0),
                    file_type=att.get('file_type', ''),
                    uploaded_at=to_db_datetime(datetime.now(timezone.utc)),
                    width=att.get('width'),
                    height=att.get('height'),
                    duration=att.get('duration'),
                )
                self.session.add(attachment)

            await self.session.commit()

        return {
            "type": "message",
            "id": msg.id,
            "nickname": sanitize_input(nickname),
            "content": sanitize_input(content),
            "channel": channel,
            "time": to_db_datetime(datetime.now(timezone.utc)).isoformat(),
            "sender_id": user_id,
            "status": "sent",
            "attachments": attachments if attachments else [],
        }

    async def get_profile_stats(self, user_id: int) -> Dict[str, int]:
        """
        Получение статистики профиля.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Статистика
        """
        messages_result = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where((Message.user_id == user_id))
        )
        messages_count = messages_result.scalar() or 0

        channels_result = await self.session.execute(
            select(func.count())
            .select_from(Channel)
            .where(Channel.creator_id == user_id)
            .where(Channel.is_active.is_(True))
        )
        channels_count = channels_result.scalar() or 0

        return {
            "messages_count": messages_count,
            "channels_count": channels_count,
        }