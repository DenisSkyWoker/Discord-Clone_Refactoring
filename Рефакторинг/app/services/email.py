#!/usr/bin/env python3
"""
=============================================================================
APP SERVICES EMAIL
Email сервис для отправки уведомлений
=============================================================================
"""
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from loguru import logger

from app.core.config import get_settings
from app.utils.helpers import sanitize_input
from app.utils.logging import get_logger
from app.utils.security_logger import log_security_event

logger = get_logger(__name__)
settings = get_settings()


async def send_verification_email(
        email: str,
        code: str,
        nickname: str,
) -> bool:
    """
    Отправка email с кодом подтверждения.
    
    Args:
        email: Email адрес получателя
        code: Код подтверждения
        nickname: Никнейм пользователя
        
    Returns:
        bool: True если отправлено успешно
    """
    try:
        logger.info(f"📧 [EMAIL] Начало отправки: {email}")
        logger.debug(f"👤 [EMAIL] Никнейм: {nickname}")
        logger.debug(f"🔢 [EMAIL] Код: {code[:2]}**")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Подтверждение email - {settings.APP_NAME}"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = email

        text_content = f"Здравствуйте, {nickname}! Ваш код подтверждения: {code}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #36393f; color: #dcddde; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #2f3136; padding: 30px; border-radius: 8px;">
                <h2 style="color: #5865F2;">Подтверждение email</h2>
                <p>Здравствуйте, <strong>{sanitize_input(nickname)}</strong>!</p>
                <p>Ваш код подтверждения:</p>
                <div style="background-color: #202225; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #5865F2; letter-spacing: 5px;">{code}</span>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        logger.info(f"📡 [SMTP] Подключение к {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        logger.debug(f"🔐 [SMTP] TLS: {settings.smtp_use_tls}")
        logger.debug(f"👤 [SMTP] User: {settings.SMTP_USER}")
        logger.info("📡 [SMTP] Отправка письма...")

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=int(settings.SMTP_PORT),
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.smtp_use_tls,
        )

        logger.success(f"✅ [EMAIL] Email отправлен: {email}")

        log_security_event(
            "EMAIL_SENT",
            {
                "email": email,
                "nickname": nickname,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
            },
        )

        return True

    except aiosmtplib.errors.SMTPConnectError as e:
        logger.error(f"❌ [SMTP] Ошибка подключения: {e}")
        logger.error(f"❌ [SMTP] Хост: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        logger.exception(f"Stack trace: {traceback.format_exc()}")
        return False

    except aiosmtplib.errors.SMTPAuthenticationError as e:
        logger.error(f"❌ [SMTP] Ошибка аутентификации: {e}")
        logger.error(f"❌ [SMTP] Проверьте SMTP_USER и SMTP_PASSWORD")
        logger.exception(f"Stack trace: {traceback.format_exc()}")
        return False

    except Exception as e:
        logger.error(f"❌ [EMAIL] Ошибка отправки email: {e}")
        logger.error(f"❌ [EMAIL] Тип ошибки: {type(e).__name__}")
        logger.exception(f"Stack trace: {traceback.format_exc()}")
        return False