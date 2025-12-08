"""
Обработчик команды /start.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.bot.application.keyboard import get_main_menu_keyboard
from src.bot.application.context import get_bot_context

logger = logging.getLogger(__name__)


async def start_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды /start.
    Доступна менеджерам и выше.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_name = message.from_user.first_name
    username = message.from_user.username
    user_id = message.from_user.id
    
    # Получаем роль пользователя для отображения соответствующих кнопок
    context = get_bot_context()
    user_role = await context.access_service.get_user_role(user_id)
    
    welcome_text = (
        f"Привет, {user_name}! 👋\n\n"
        "Я бот для управления черным списком арендаторов.\n\n"
        "📋 Основные возможности:\n"
        "• Просмотр черного списка\n"
        "• Добавление арендаторов в черный список\n"
        "• Управление записями\n\n"
        "Выберите действие из меню ниже."
    )
    
    # Отправляем приветствие с клавиатурой главного меню (с учетом прав доступа)
    await bot.reply_to(message, welcome_text, reply_markup=get_main_menu_keyboard(user_role))
    logger.info(f"Команда /start выполнена для пользователя {user_id} (@{username}) с ролью {user_role.value if user_role else 'неизвестна'}")

