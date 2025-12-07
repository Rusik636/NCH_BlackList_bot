"""
Обработчик команды /start.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.bot.application.keyboard import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def start_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды /start.
    Доступна всем пользователям.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_name = message.from_user.first_name
    username = message.from_user.username
    
    welcome_text = (
        f"Привет, {user_name}! 👋\n\n"
        "Я бот для управления черным списком арендаторов.\n\n"
        "📋 Основные возможности:\n"
        "• Просмотр черного списка\n"
        "• Добавление арендаторов в черный список\n"
        "• Управление записями\n\n"
        "Выберите действие из меню ниже."
    )
    
    # Отправляем приветствие с клавиатурой главного меню
    await bot.reply_to(message, welcome_text, reply_markup=get_main_menu_keyboard())
    logger.info(f"Команда /start выполнена для пользователя {message.from_user.id} (@{username})")

