#!/usr/bin/env python3
"""
=============================================================================
APP DB HEALTH
Проверка здоровья базы данных
=============================================================================
"""
import time
from typing import Dict, Any, List

from sqlalchemy import text
from loguru import logger

from app.db.session import engine
from app.db.models import Base


async def check_database_health() -> Dict[str, Any]:
    """
    Проверка подключения и состояния базы данных.
    
    Returns:
        Dict: Результат проверки
    """
    result: Dict[str, Any] = {
        "success": False,
        "connection": False,
        "tables": False,
        "permissions": False,
        "errors": [],
    }

    try:
        # =========================================================================
        # ПРОВЕРКА ПОДКЛЮЧЕНИЯ
        # =========================================================================
        start_time = time.time()
        async with engine.connect() as conn:
            db_version_result = await conn.execute(text("SELECT version()"))
            db_version = db_version_result.scalar()
            elapsed = int((time.time() - start_time) * 1000)

            if db_version is None:
                raise Exception("Не удалось получить версию PostgreSQL")

            result["connection"] = True
            logger.success(f"✅ Подключение успешно: {db_version[:50]}...")
            logger.info(f"🔌 Проверка подключения к PostgreSQL... - Ok ({elapsed}ms)")

        # =========================================================================
        # ПРОВЕРКА ПРАВ ДОСТУПА
        # =========================================================================
        start_time = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("CREATE TABLE IF NOT EXISTS _health_check (id INTEGER)"))
            await conn.execute(text("INSERT INTO _health_check VALUES (1)"))
            await conn.execute(text("DELETE FROM _health_check WHERE id = 1"))
            await conn.execute(text("DROP TABLE IF EXISTS _health_check"))
            elapsed = int((time.time() - start_time) * 1000)

            result["permissions"] = True
            logger.success("✅ Права доступа подтверждены (CREATE/INSERT/DELETE)")
            logger.info(f"🔐 Проверка прав доступа... - Ok ({elapsed}ms)")

        # =========================================================================
        # ПРОВЕРКА ТАБЛИЦ
        # =========================================================================
        start_time = time.time()
        async with engine.connect() as conn:
            tables_result = await conn.execute(text("""
                                                    SELECT table_name FROM information_schema.tables
                                                    WHERE table_schema = 'public'
                                                      AND table_name IN (
                                                                         'registered_users', 'email_verification_codes', 'connected_users',
                                                                         'messages', 'security_logs', 'channels', 'message_statuses',
                                                                         'message_attachments', 'password_reset_tokens'
                                                        )
                                                    """))
            existing_tables = [row[0] for row in tables_result.fetchall()]
            elapsed = int((time.time() - start_time) * 1000)

            required_tables = {
                'registered_users', 'messages', 'channels',
                'connected_users', 'security_logs'
            }

            if required_tables.issubset(set(existing_tables)):
                result["tables"] = True
                logger.success("✅ Все необходимые таблицы существуют")
            else:
                missing = required_tables - set(existing_tables)
                result["errors"].append(f"Отсутствуют таблицы: {missing}")
                logger.warning(f"⚠️ Отсутствуют таблицы: {missing}")

            logger.info(f"📋 Проверка таблиц... - Ok ({elapsed}ms)")

    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"❌ Ошибка проверки БД: {e}")

    result["success"] = all([result["connection"], result["permissions"]])
    return result