"""
Обработчик редактирования записей черного списка.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.bot.application.keyboard import get_main_menu_keyboard
from src.bot.application.context import get_bot_context

logger = logging.getLogger(__name__)


async def edit_blacklist_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик кнопки "Редактировать ЧС".
    Доступен только админам и выше.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    logger.info(f"Пользователь {user_id} начал редактирование ЧС")
    
    # Получаем роль пользователя для отображения соответствующей клавиатуры
    context = get_bot_context()
    user_role = await context.access_service.get_user_role(user_id)
    
    # TODO: Реализовать функционал редактирования записей черного списка
    # Заготовка для будущей реализации
    
    await bot.reply_to(
        message,
        "🔧 <b>Редактирование черного списка</b>\n\n"
        "Функционал находится в разработке.\n"
        "Здесь будет возможность редактировать записи черного списка.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(user_role),
    )

