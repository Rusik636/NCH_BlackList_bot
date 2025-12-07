"""
Регистрация обрабочиков Telegram бота.
"""
import logging
from typing import Any

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

logger = logging.getLogger(__name__)

def register_handlers(bot: AsyncTeleBot) -> None:
    """
    Регистрация всех обработчиков команд и сообщений.
    
    Args:
        bot: Экземпляр бота для регистрации обработчиков
    """
    # Регистрация команд пример
    # bot.message_handler(commands=["start"])(start_handler)
    # bot.message_handler(commands=["help"])(help_handler)
    
    # # Регистрация обработчика текстовых сообщений
    # bot.message_handler(content_types=["text"])(text_handler)
    
    logger.info("Обработчики бота зарегистрированы")

