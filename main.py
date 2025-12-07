"""
Точка входа в приложение Telegram бота.
Инициализирует бота и подключение к базе данных.
"""
import asyncio
import logging
import sys
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_helper

from src.config import get_config
from src.db.connection import DatabaseManager
from src.db.table import initialize_tables
from src.bot.application.register_handlers import register_handlers

# Логирование настраивается автоматически при загрузке конфигурации
logger = logging.getLogger(__name__)


class BotApplication:
    """Основной класс приложения бота."""
    
    def __init__(self):
        """Инициализация приложения."""
        self.config = get_config()
        self.bot: Optional[AsyncTeleBot] = None
        self.db_manager: Optional[DatabaseManager] = None
    
    async def initialize_database(self) -> None:
        """Инициализация подключения к базе данных."""
        try:
            logger.info("Инициализация подключения к базе данных...")
            self.db_manager = DatabaseManager(self.config.database)
            await self.db_manager.initialize()
            logger.info("Подключение к базе данных установлено")
            
            # Инициализация таблиц
            await initialize_tables(self.db_manager)
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации БД: {e}", exc_info=True)
            raise
    
    async def initialize_bot(self) -> None:
        """Инициализация Telegram бота."""
        try:
            logger.info("Инициализация Telegram бота...")
            self.bot = AsyncTeleBot(self.config.bot.token)
            
            # Регистрация обработчиков
            register_handlers(self.bot)
            
            logger.info("Бот инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации бота: {e}", exc_info=True)
            raise
    
    async def start(self) -> None:
        """Запуск приложения."""
        try:
            # Инициализация БД
            await self.initialize_database()
            
            # Инициализация бота
            await self.initialize_bot()
            
            if not self.bot:
                raise RuntimeError("Бот не инициализирован")
            
            logger.info("Запуск бота...")
            await self.bot.polling(non_stop=True, interval=0, timeout=20)
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Очистка ресурсов при завершении работы."""
        logger.info("Очистка ресурсов...")
        
        if self.db_manager:
            await self.db_manager.close()
        
        if self.bot:
            await asyncio_helper.session_manager.close_session()
        
        logger.info("Ресурсы освобождены")


async def main() -> None:
    """Главная функция запуска приложения."""
    app = BotApplication()
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)

