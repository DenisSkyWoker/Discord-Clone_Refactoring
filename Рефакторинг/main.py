#!/usr/bin/env python3
"""
Discord Clone - Точка входа
Только запуск приложения, вся логика в app/
"""
import hashlib
from pathlib import Path

import uvicorn
from loguru import logger

from app.core.config import get_settings
from app.utils.logging import setup_logger

# Настройка логгера
setup_logger()
settings = get_settings()

logger.info(f"🔐 SECRET_KEY hash: {hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:16]}...")


if __name__ == "__main__":
    ssl_kwargs = {}

    # Настройка TLS/SSL
    if settings.USE_TLS:
        cert_path = Path("Certs") / settings.SSL_CERT_FILE
        key_path = Path("Certs") / settings.SSL_KEY_FILE

        if cert_path.exists() and key_path.exists():
            ssl_kwargs = {
                "ssl_keyfile": str(key_path),
                "ssl_certfile": str(cert_path),
            }
            logger.info("🔒 TLS/SSL включен")
        else:
            logger.error("❌ Файлы сертификатов не найдены!")
            raise FileNotFoundError("SSL certificates not found")
    else:
        logger.warning("⚠️ TLS/SSL выключен")

    logger.info(f"🚀 Запуск сервера на {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        **ssl_kwargs,
    )