    #!/usr/bin/env python3
"""
=============================================================================
DISCORD CLONE - CONFIGURATION
Настройки приложения из .env файла
=============================================================================
"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# =============================================================================
# БАЗОВЫЕ ПУТИ (до объявления класса)
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):

    """
Настройки приложения Discord Clone.
Значения загружаются из переменных окружения или .env файла.
"""

# =============================================================================
# ПРИЛОЖЕНИЕ
# =============================================================================
APP_NAME: str = "Discord Clone Server"
DEBUG_MODE: bool = True

# =============================================================================
# СЕТЬ
# =============================================================================
HOST: str = "192.168.1.110"
PORT: int = 8000
USE_TLS: bool = True
SSL_CERT_FILE: str = "cert.pem"
SSL_KEY_FILE: str = "key.pem"

# =============================================================================
# БЕЗОПАСНОСТЬ
# =============================================================================
SECRET_KEY: str = "8h3m6YCyWKY_PZDYV_C_oEL7sw28ahJsYMqATK1_iD0"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# Защита от brute force
MAX_LOGIN_ATTEMPTS: int = 5
LOGIN_LOCKOUT_MINUTES: int = 15

# Требования к паролю
MIN_PASSWORD_LENGTH: int = 8
REQUIRE_SPECIAL_CHARS: bool = True

# CORS (разрешённые домены)
ALLOWED_ORIGINS: str = "https://192.168.1.110:8000"

# Rate Limiting
RATE_LIMIT_PER_MINUTE: int = 60

# Сессии
SESSION_TIMEOUT_MINUTES: int = 30
SECURE_COOKIES: bool = False

# =============================================================================
# БАЗА ДАННЫХ (PostgreSQL)
# =============================================================================
DB_USER: str = "postgres"
DB_PASSWORD: str = "Aa210801"
DB_HOST: str = "192.168.1.110"
DB_PORT: int = 5432
DB_NAME: str = "discord_clone"

# Параметры пула соединений
DB_POOL_SIZE: int = 5
DB_MAX_OVERFLOW: int = 10

# =============================================================================
# EMAIL (SMTP)
# =============================================================================
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = "hulk9135@gmail.com"
SMTP_PASSWORD: str = "eciv ssze ehrx ykyi"
SMTP_FROM_NAME: str = "Discord Clone"
SMTP_USE_TLS: str = "true"
VERIFICATION_CODE_EXPIRE_MINUTES: int = 15

# =============================================================================
# ЛОГИРОВАНИЕ
# =============================================================================
LOG_LEVEL: str = "INFO"
LOG_FILE: str = "logs/server.log"
LOG_ROTATION: str = "00:00"
LOG_RETENTION: str = "7 days"

# =============================================================================
# Настройки загрузки файлов
# =============================================================================
MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10 MB по умолчанию
ALLOWED_IMAGE_TYPES: str = os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/gif,image/webp")
ALLOWED_VIDEO_TYPES: str = os.getenv("ALLOWED_VIDEO_TYPES", "video/mp4,video/webm,video/quicktime")
ALLOWED_AUDIO_TYPES: str = os.getenv("ALLOWED_AUDIO_TYPES", "audio/mpeg,audio/ogg,audio/wav")
ALLOWED_DOCUMENT_TYPES: str = os.getenv("ALLOWED_DOCUMENT_TYPES", "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document")
UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")


# =============================================================================
# ВЫЧИСЛЯЕМЫЕ СВОЙСТВА
# =============================================================================
@property
def certs_dir(self) -> Path:
    """Полный путь к папке с SSL сертификатами"""
    return PROJECT_ROOT / "Certs"

@property
def ssl_cert_path(self) -> Path:
    """Полный путь к SSL сертификату"""
    return self.certs_dir / self.SSL_CERT_FILE

@property
def ssl_key_path(self) -> Path:
    """Полный путь к SSL ключу"""
    return self.certs_dir / self.SSL_KEY_FILE

@property
def database_url(self) -> str:
    """Строка подключения к базе данных"""
    return (
        f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
        f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    )

@property
def log_file_path(self) -> Path:
    """Полный путь к файлу логов"""
    return BASE_DIR / self.LOG_FILE

@property
def static_dir_path(self) -> Path:
    """Полный путь к папке статики"""
    return BASE_DIR / "static"

# =============================================================================
# КОНФИГУРАЦИЯ PYDANTIC V2 ✅
# =============================================================================
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True,
    extra="ignore",
)


@lru_cache()
def get_settings() -> Settings:
    """Кэширует настройки"""
    return Settings()


# =============================================================================
# ПРОВЕРКА КОНФИГУРАЦИИ
# =============================================================================

if __name__ == "__main__":
    settings = get_settings()
    print("=" * 70)
    print("📊 DISCORD CLONE - КОНФИГУРАЦИЯ")
    print("=" * 70)
    print(f"📂 BASE_DIR:         {BASE_DIR}")
    print(f"📂 PROJECT_ROOT:     {PROJECT_ROOT}")
    print(f"📂 CERTS_DIR:        {settings.certs_dir}")
    print(f"📄 SSL_CERT:         {settings.ssl_cert_path}")
    print(f"🔑 SSL_KEY:          {settings.ssl_key_path}")
    print(f"📂 LOGS_DIR:         {settings.log_file_path.parent}")
    print(f"📄 LOG_FILE:         {settings.log_file_path}")
    print(f"📂 STATIC_DIR:       {settings.static_dir_path}")
    print(f"🔐 TLS:              {settings.USE_TLS}")
    print(f"🗄️ БД:                {settings.database_url}")
    print("=" * 70)

    print("\n🔍 ПРОВЕРКА ФАЙЛОВ:")
    print(f"  SSL сертификат: {'✅' if settings.ssl_cert_path.exists() else '❌'}")
    print(f"  SSL ключ:       {'✅' if settings.ssl_key_path.exists() else '❌'}")
    print(
        f"  Папка логов:    {'✅' if settings.log_file_path.parent.exists() else '❌'}"
    )
    print(f"  Папка статики:  {'✅' if settings.static_dir_path.exists() else '❌'}")
    print("=" * 70)
