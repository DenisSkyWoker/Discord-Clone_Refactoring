#!/usr/bin/env python3
"""
=============================================================================
APP DB MIGRATIONS
Миграции базы данных
=============================================================================
"""
import time
from sqlalchemy import text
from loguru import logger

from app.db.session import engine
from app.db.models import Base


async def run_migrations() -> None:
    """
    Применение миграций базы данных.
    """
    logger.info("🔧 Применение миграций...")
    total_start = time.time()

    try:
        async with engine.connect() as conn:
            async with conn.begin():
                # =========================================================================
                # СОЗДАНИЕ ТАБЛИЦ
                # =========================================================================
                await conn.run_sync(Base.metadata.create_all)
                logger.success("✅ Таблицы созданы")

                # =========================================================================
                # МИГРАЦИЯ: registered_users
                # =========================================================================
                await conn.execute(text("""
                                        ALTER TABLE registered_users
                                            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE
                                        """))

                await conn.execute(text("""
                                        ALTER TABLE registered_users
                                            ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0
                                        """))

                await conn.execute(text("""
                                        ALTER TABLE registered_users
                                            ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP
                                        """))

                await conn.execute(text("""
                                        ALTER TABLE registered_users
                                            ADD COLUMN IF NOT EXISTS last_ip VARCHAR(45)
                                        """))

                await conn.execute(text("""
                                        ALTER TABLE registered_users
                                            ADD COLUMN IF NOT EXISTS session_token VARCHAR(255)
                                        """))

                logger.success("✅ Миграции registered_users применены")

                # =========================================================================
                # МИГРАЦИЯ: messages
                # =========================================================================
                await conn.execute(text("""
                                        ALTER TABLE messages
                                            ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE
                                        """))

                await conn.execute(text("""
                                        ALTER TABLE messages
                                            ADD COLUMN IF NOT EXISTS edited BOOLEAN DEFAULT FALSE
                                        """))

                logger.success("✅ Миграции messages применены")

                # =========================================================================
                # ТАБЛИЦА: message_statuses
                # =========================================================================
                await conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS message_statuses (
                                                                                        id SERIAL PRIMARY KEY,
                                                                                        message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                                            user_id INTEGER NOT NULL REFERENCES registered_users(id) ON DELETE CASCADE,
                                            is_delivered BOOLEAN DEFAULT FALSE,
                                            is_read BOOLEAN DEFAULT FALSE,
                                            delivered_at TIMESTAMP,
                                            read_at TIMESTAMP,
                                            UNIQUE(message_id, user_id)
                                            )
                                        """))

                logger.success("✅ Таблица message_statuses создана")

                # =========================================================================
                # ТАБЛИЦА: message_attachments
                # =========================================================================
                await conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS message_attachments (
                                                                                           id SERIAL PRIMARY KEY,
                                                                                           message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                                            file_name VARCHAR(255) NOT NULL,
                                            file_path VARCHAR(500) NOT NULL,
                                            file_size BIGINT NOT NULL,
                                            file_type VARCHAR(100) NOT NULL,
                                            uploaded_at TIMESTAMP DEFAULT NOW(),
                                            width INTEGER,
                                            height INTEGER,
                                            duration INTEGER
                                            )
                                        """))

                logger.success("✅ Таблица message_attachments создана")

                # =========================================================================
                # ТАБЛИЦА: password_reset_tokens
                # =========================================================================
                await conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS password_reset_tokens (
                                                                                             id SERIAL PRIMARY KEY,
                                                                                             user_id INTEGER NOT NULL REFERENCES registered_users(id) ON DELETE CASCADE,
                                            token_hash VARCHAR(64) NOT NULL UNIQUE,
                                            created_at TIMESTAMP DEFAULT NOW(),
                                            expires_at TIMESTAMP NOT NULL,
                                            is_used BOOLEAN DEFAULT FALSE,
                                            ip_address VARCHAR(45)
                                            )
                                        """))

                logger.success("✅ Таблица password_reset_tokens создана")

                # =========================================================================
                # ИНДЕКСЫ
                # =========================================================================
                await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS idx_user_nickname ON registered_users(nickname)
                                        """))

                await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS idx_user_email ON registered_users(email)
                                        """))

                await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS idx_message_channel ON messages(channel, created_at)
                                        """))

                await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS idx_channel_name ON channels(name, is_active)
                                        """))

                logger.success("✅ Индексы созданы")

        total_elapsed = int((time.time() - total_start) * 1000)
        logger.info(f"⏱️ Общее время миграций: {total_elapsed}ms")
        logger.success("✅ Все миграции применены успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка при применении миграций: {e}")
        raise