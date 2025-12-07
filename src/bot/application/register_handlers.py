"""
Регистрация обработчиков Telegram бота.
"""
import logging

from telebot.async_telebot import AsyncTeleBot

from src.bot.application.context import BotContext
from src.bot.application.decorators import require_role
from src.bot.domain.role import Role
from src.bot.application.handlers import start_handler, id_handler

logger = logging.getLogger(__name__)


def register_handlers(bot: AsyncTeleBot, context: BotContext) -> None:
    """
    Регистрация всех обработчиков команд и сообщений.
    
    Args:
        bot: Экземпляр бота для регистрации обработчиков
        context: Контекст приложения с зависимостями
    """
    access_service = context.access_service
    
    # Публичные команды (доступны всем пользователям)
    bot.message_handler(commands=["id"], pass_bot=True)(id_handler)
    
    # Команды с ограничением доступа по ролям
    # Команда /start доступна менеджерам и выше (MANAGER, ADMIN, SUPER_ADMIN)
    bot.message_handler(commands=["start"], pass_bot=True)(
        require_role(Role.MANAGER, access_service)(start_handler)
    )
    
    logger.info("Обработчики бота зарегистрированы")
