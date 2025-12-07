"""
Конфигурация приложения.
Загружает переменные окружения из .env файла.
"""
import os
import sys
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @property
    def connection_string(self) -> str:
        """Возвращает строку подключения к БД."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class BotConfig:
    """Конфигурация Telegram бота."""
    token: str
    admin_ids: list[int]
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Создает конфигурацию бота из переменных окружения."""
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [
            int(admin_id.strip()) 
            for admin_id in admin_ids_str.split(",") 
            if admin_id.strip()
        ]
        
        return cls(token=token, admin_ids=admin_ids)


@dataclass
class SecurityConfig:
    """Конфигурация безопасности для хеширования персональных данных."""
    hash_pepper: str
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Создает конфигурацию безопасности из переменных окружения."""
        hash_pepper = os.getenv("HASH_PEPPER")
        if not hash_pepper:
            raise ValueError(
                "HASH_PEPPER не установлен в переменных окружения. "
                "Сгенерируйте случайную строку минимум 32 символа."
            )
        
        if len(hash_pepper) < 32:
            raise ValueError("HASH_PEPPER должен быть минимум 32 символа")
        
        return cls(hash_pepper=hash_pepper)


@dataclass
class Config:
    """Основная конфигурация приложения."""
    bot: BotConfig
    database: DatabaseConfig
    security: SecurityConfig
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "Config":
        """Создает конфигурацию из переменных окружения."""
        bot = BotConfig.from_env()
        
        database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "lict_rent"),
        )
        
        security = SecurityConfig.from_env()
        
        debug = os.getenv("DEBUG", "False").lower() == "true"
        
        return cls(bot=bot, database=database, security=security, debug=debug)


# Глобальный экземпляр конфигурации
config: Optional[Config] = None


def setup_logging(level: Optional[str] = None, format_string: Optional[str] = None) -> None:
    """
    Настройка логирования приложения.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Если не указан, берется из переменной окружения LOG_LEVEL или INFO.
        format_string: Формат строки логирования. Если не указан, используется стандартный.
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Преобразуем строку уровня в константу logging
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Перезаписываем существующую конфигурацию
    )


def get_config() -> Config:
    """Получить конфигурацию приложения (singleton)."""
    global config
    if config is None:
        # Настраиваем логирование при первой загрузке конфигурации
        setup_logging()
        config = Config.from_env()
    return config

