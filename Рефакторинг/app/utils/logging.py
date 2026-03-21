#!/usr/bin/env python3
"""
Настройка логгера для всего приложения
"""
import sys
from pathlib import Path
from loguru import logger
from app.core.config import get_settings


def setup_logger() -> logger:
    """Настройка логгера для всего приложения."""
    settings = get_settings()

    # Удаляем стандартный обработчик
    logger.remove()

    # Создаем директорию для логов
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Файловый логгер
    logger.add(
        settings.LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        format="{time:DD-MM-YYYY HH:mm:ss} | {level: <8} | {module}:{function}:{line} - {message}",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    # Консольный логгер
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:DD-MM-YYYY HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}:{function}:{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    return logger


def get_logger(name: str = __name__):
    """Получение логгера для модуля."""
    return logger