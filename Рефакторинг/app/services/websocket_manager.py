#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES WEBSOCKET MANAGER
Менеджер WebSocket подключений
=============================================================================
"""
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from loguru import logger
from starlette.websockets import WebSocketState

from app.db.session import async_session_maker
from app.utils.logging import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


class ConnectionManager:
    """Управление активными WebSocket подключениями."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.user_nicks: Dict[WebSocket, str] = {}
        self.user_channels: Dict[WebSocket, str] = {}
        self.user_ids: Dict[WebSocket, int] = {}
        self.channels: Dict[str, Set[WebSocket]] = {
            "общий-чат": set(),
            "флудилка": set(),
            "мемы": set(),
        }

    async def connect(
            self,
            websocket: WebSocket,
            nickname: str,
            channel: str = "общий-чат",
            user_id: Optional[int] = None,
    ) -> None:
        """
        Подключение нового пользователя.
        
        Args:
            websocket: WebSocket соединение
            nickname: Никнейм пользователя
            channel: Канал для подключения
            user_id: ID пользователя
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_nicks[websocket] = nickname
        self.user_channels[websocket] = channel

        if user_id:
            self.user_ids[websocket] = user_id

        if channel not in self.channels:
            self.channels[channel] = set()
            logger.info(f"✅ Канал {channel} добавлен в менеджер подключений")

        self.channels[channel].add(websocket)
        logger.info(f"Пользователь {nickname} подключился к каналу {channel}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Отключение пользователя с очисткой ресурсов.
        
        Args:
            websocket: WebSocket соединение
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            nick = self.user_nicks.pop(websocket, "Unknown")
            channel = self.user_channels.pop(websocket, "общий-чат")
            user_id = self.user_ids.pop(websocket, None)

            if channel in self.channels:
                self.channels[channel].discard(websocket)

            logger.info(f"Пользователь {nick} отключился от канала {channel}")

            # Обновление статуса в БД
            if user_id:
                try:
                    async with async_session_maker() as session:
                        await session.execute(
                            text("""
                                 UPDATE connected_users
                                 SET is_online = FALSE
                                 WHERE user_id = :user_id AND is_online = TRUE
                                 """),
                            {"user_id": user_id},
                        )
                        await session.commit()
                except Exception as e:
                    logger.error(f"Ошибка обновления статуса: {e}")

            # Закрытие сокета с обработкой ошибок
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except RuntimeError as e:
                if "already closed" in str(e).lower():
                    logger.debug(f"⚪ Сокет уже закрыт для {nick}")
                else:
                    logger.warning(f"⚠️ Ошибка закрытия сокета {nick}: {e}")
            except ConnectionResetError:
                logger.debug(f"⚪ Клиент {nick} уже разорвал соединение")
            except Exception as e:
                logger.warning(f"⚠️ Неожиданная ошибка при закрытии сокета {nick}: {type(e).__name__}")

    async def switch_channel(self, websocket: WebSocket, new_channel: str) -> bool:
        """
        Переключение пользователя между каналами.
        
        Args:
            websocket: WebSocket соединение
            new_channel: Новый канал
            
        Returns:
            bool: True если успешно
        """
        old_channel = self.user_channels.get(websocket, "общий-чат")

        if old_channel in self.channels:
            self.channels[old_channel].discard(websocket)

        if new_channel in self.channels:
            self.channels[new_channel].add(websocket)
            self.user_channels[websocket] = new_channel
            logger.info(f"Пользователь {self.user_nicks.get(websocket)} перешёл в {new_channel}")
            return True

        return False

    async def add_channel(self, channel_name: str) -> None:
        """
        Добавить новый канал в список.
        
        Args:
            channel_name: Название канала
        """
        if channel_name not in self.channels:
            self.channels[channel_name] = set()
            logger.info(f"✅ Канал {channel_name} добавлен в менеджер")

    async def send_to_channel(self, channel: str, message: dict) -> None:
        """
        Отправка сообщения всем пользователям канала.
        
        Args:
            channel: Название канала
            message: Сообщение для отправки
        """
        logger.info(f"📤 Отправка сообщения в канал {channel}: {message.get('type')}")

        if channel in self.channels:
            connections_copy = list(self.channels[channel])
            logger.info(f"👥 В канале {channel} подключено: {len(connections_copy)} клиентов")

            sent_count = 0
            for connection in connections_copy:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                        sent_count += 1
                    else:
                        logger.warning("⚠️ Сокет не подключён, отключаем...")
                        await self.disconnect(connection)
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки сообщения: {e}")
                    try:
                        await self.disconnect(connection)
                    except Exception:
                        pass

            logger.info(f"✅ Сообщение отправлено {sent_count}/{len(connections_copy)} клиентам")
        else:
            logger.error(f"❌ Канал {channel} НЕ НАЙДЕН в менеджере! Доступные каналы: {list(self.channels.keys())}")

    async def send_to_user(self, nickname: str, message: dict) -> None:
        """
        Отправка сообщения конкретному пользователю.
        
        Args:
            nickname: Никнейм получателя
            message: Сообщение для отправки
        """
        for ws, nick in list(self.user_nicks.items()):
            if nick == nickname:
                try:
                    if ws.client_state == WebSocketState.CONNECTED:
                        await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {nickname}: {e}")

    async def broadcast_online_users(self, channel: str) -> None:
        """
        Рассылка списка онлайн пользователей.
        
        Args:
            channel: Название канала
        """
        users = []
        for ws, ch in list(self.user_channels.items()):
            if ch == channel:
                users.append(self.user_nicks.get(ws, "Unknown"))

        if channel in self.channels:
            connections_copy = list(self.channels[channel])
            for connection in connections_copy:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json({
                            "type": "online_users",
                            "users": users,
                            "channel": channel,
                        })
                    else:
                        await self.disconnect(connection)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось отправить online_users: {e}")

    def get_online_users(self, channel: str) -> List[str]:
        """
        Получение списка онлайн пользователей канала.
        
        Args:
            channel: Название канала
            
        Returns:
            List[str]: Список никнеймов
        """
        users = []
        for ws, ch in self.user_channels.items():
            if ch == channel:
                users.append(self.user_nicks.get(ws, "Unknown"))
        return users

    async def shutdown(self) -> None:
        """Закрытие всех подключений при остановке сервера."""
        logger.info(f"🔌 Закрытие {len(self.active_connections)} WebSocket подключений...")

        for connection in self.active_connections[:]:
            try:
                await self.disconnect(connection)
            except Exception as e:
                logger.error(f"Ошибка закрытия подключения: {e}")

        logger.success("✅ Все WebSocket подключения закрыты")


# Глобальный экземпляр менеджера
manager = ConnectionManager()