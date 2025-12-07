"""
Регистрация обработчиков Telegram бота.
"""
import logging

from telebot.async_telebot import AsyncTeleBot

from src.bot.application.context import BotContext
from src.bot.application.decorators import require_role
from src.bot.domain.role import Role
from src.bot.application.keyboard import BTN_ADD_TO_BLACKLIST
from src.bot.application.storage import user_state_storage
from src.bot.application.handlers import (
    start_handler,
    id_handler,
    add_to_blacklist_handler,
    blacklist_message_handler,
    blacklist_callback_handler,
    cancel_collection_handler,
)
from src.bot.application.handlers.blacklist.keyboards import (
    BTN_CANCEL_PROCESS,
    CALLBACK_CONFIRM_ADD,
    CALLBACK_EDIT,
    CALLBACK_CANCEL,
    CALLBACK_REASON_PREFIX,
)

logger = logging.getLogger(__name__)


def register_handlers(bot: AsyncTeleBot, context: BotContext) -> None:
    """
    Регистрация всех обработчиков команд и сообщений.
    
    Args:
        bot: Экземпляр бота для регистрации обработчиков
        context: Контекст приложения с зависимостями
    """
    access_service = context.access_service
    
    # =====================================================
    # Публичные команды (доступны всем пользователям)
    # =====================================================
    bot.message_handler(commands=["id"], pass_bot=True)(id_handler)
    
    # =====================================================
    # Команды с ограничением доступа по ролям
    # =====================================================
    
    # Команда /start доступна менеджерам и выше (MANAGER, ADMIN, SUPER_ADMIN)
    bot.message_handler(commands=["start"], pass_bot=True)(
        require_role(Role.MANAGER, access_service)(start_handler)
    )
    
    # =====================================================
    # Обработчики черного списка (доступны админам и выше)
    # =====================================================
    
    # Кнопка "Добавить в ЧС" — начало процесса сбора данных
    bot.message_handler(
        func=lambda m: m.text == BTN_ADD_TO_BLACKLIST,
        pass_bot=True
    )(require_role(Role.ADMIN, access_service)(add_to_blacklist_handler))
    
    # Кнопка "Прервать процесс" — отмена сбора данных
    bot.message_handler(
        func=lambda m: m.text == BTN_CANCEL_PROCESS,
        pass_bot=True
    )(cancel_collection_handler)
    
    # Callback-обработчик для инлайн-кнопок (подтверждение и выбор причины)
    @bot.callback_query_handler(
        func=lambda call: (
            call.data in [CALLBACK_CONFIRM_ADD, CALLBACK_EDIT, CALLBACK_CANCEL]
            or call.data.startswith(CALLBACK_REASON_PREFIX)
        )
    )
    async def _blacklist_callback_wrapper(call):
        await blacklist_callback_handler(call, bot)
    
    # Обработчик сообщений во время сбора данных
    # Важно: этот обработчик должен быть последним, чтобы не перехватывать другие сообщения
    @bot.message_handler(
        func=lambda m: True,  # Фильтрация происходит внутри
        pass_bot=True
    )
    async def _blacklist_message_wrapper(message, bot):
        # Проверяем, находится ли пользователь в процессе сбора данных
        if await user_state_storage.is_collecting(message.from_user.id):
            await blacklist_message_handler(message, bot)
    
    logger.info("Обработчики бота зарегистрированы")