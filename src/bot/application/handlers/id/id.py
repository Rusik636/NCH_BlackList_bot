"""
Обработчик команды /id.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

logger = logging.getLogger(__name__)


async def id_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик команды /id.
    Показывает Telegram ID пользователя.
    Доступна всем пользователям (публичная команда).
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Формируем полное имя
    full_name = first_name
    if last_name:
        full_name += f" {last_name}"
    
    # Формируем сообщение
    id_text = (
        f"🆔 Ваш Telegram ID:\n\n"
        f"<code>{user_id}</code>\n\n"
        f"👤 Имя: {full_name}\n"
    )
    
    if username:
        id_text += f"📱 Username: @{username}\n"
    
    await bot.reply_to(message, id_text, parse_mode="HTML")
    logger.info(f"Команда /id выполнена для пользователя {user_id} (@{username})")

