"""
Регистрация обработчиков Telegram бота.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.bot.application.context import BotContext
from src.bot.application.decorators import require_role
from src.bot.domain.role import Role

logger = logging.getLogger(__name__)


async def start_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды /start.
    Доступна всем пользователям.
    """
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот для управления черным списком арендаторов.\n"
        "Используйте /help для списка доступных команд."
    )
    await bot.reply_to(message, welcome_text)


async def help_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды /help.
    Доступна всем пользователям.
    """
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/manager_command - Команда для менеджеров\n"
        "/admin_command - Команда для администраторов\n"
        "/super_admin_command - Команда для супер администраторов\n"
    )
    await bot.reply_to(message, help_text)


async def manager_command_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды для менеджеров.
    Доступна: MANAGER, ADMIN, SUPER_ADMIN
    """
    response = (
        "✅ Команда для менеджеров выполнена.\n\n"
        "Эта команда доступна менеджерам и вышестоящим ролям."
    )
    await bot.reply_to(message, response)


async def admin_command_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды для администраторов.
    Доступна: ADMIN, SUPER_ADMIN
    """
    response = (
        "✅ Команда для администраторов выполнена.\n\n"
        "Эта команда доступна администраторам и супер администраторам."
    )
    await bot.reply_to(message, response)


async def super_admin_command_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды для супер администраторов.
    Доступна: SUPER_ADMIN
    """
    response = (
        "✅ Команда для супер администраторов выполнена.\n\n"
        "Эта команда доступна только супер администраторам."
    )
    await bot.reply_to(message, response)


def register_handlers(bot: AsyncTeleBot, context: BotContext) -> None:
    """
    Регистрация всех обработчиков команд и сообщений.
    
    Args:
        bot: Экземпляр бота для регистрации обработчиков
        context: Контекст приложения с зависимостями
    """
    access_service = context.access_service
    
    # Команды без ограничений доступа
    bot.message_handler(commands=["start"], pass_bot=True)(start_handler)
    bot.message_handler(commands=["help"], pass_bot=True)(help_handler)
    
    # Команды с ограничением доступа по ролям
    # Менеджер и выше (MANAGER, ADMIN, SUPER_ADMIN)
    bot.message_handler(commands=["manager_command"], pass_bot=True)(
        require_role(Role.MANAGER, access_service)(manager_command_handler)
    )
    
    # Администратор и выше (ADMIN, SUPER_ADMIN)
    bot.message_handler(commands=["admin_command"], pass_bot=True)(
        require_role(Role.ADMIN, access_service)(admin_command_handler)
    )
    
    # Только супер администратор (SUPER_ADMIN)
    bot.message_handler(commands=["super_admin_command"], pass_bot=True)(
        require_role(Role.SUPER_ADMIN, access_service)(super_admin_command_handler)
    )
    
    logger.info("Обработчики бота зарегистрированы")
