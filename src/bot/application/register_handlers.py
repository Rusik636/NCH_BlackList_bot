"""
Регистрация обработчиков Telegram бота.
"""
import logging

from telebot.async_telebot import AsyncTeleBot

from src.bot.application.context import BotContext
from src.bot.application.decorators import require_role
from src.bot.domain.role import Role
from src.bot.application.keyboard import BTN_ADD_TO_BLACKLIST, BTN_CHECK_USER
from src.bot.application.storage import user_state_storage
from src.bot.application.states import CheckState
from src.bot.application.handlers import (
    start_handler,
    id_handler,
    add_to_blacklist_handler,
    blacklist_message_handler,
    blacklist_callback_handler,
    cancel_collection_handler,
    check_user_handler,
    check_message_handler,
    check_callback_handler,
)
from src.bot.application.handlers.blacklist.keyboards import (
    BTN_CANCEL_PROCESS,
    CALLBACK_CONFIRM_ADD,
    CALLBACK_EDIT,
    CALLBACK_CANCEL,
    CALLBACK_REASON_PREFIX,
)
from src.bot.application.handlers.check.keyboards import (
    BTN_CANCEL_CHECK,
    CALLBACK_CHECK_CONFIRM,
    CALLBACK_CHECK_EDIT,
    CALLBACK_CHECK_CANCEL,
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
    
    # Кнопка "Прервать процесс" — отмена сбора данных добавления
    bot.message_handler(
        func=lambda m: m.text == BTN_CANCEL_PROCESS,
        pass_bot=True
    )(cancel_collection_handler)
    
    # =====================================================
    # Обработчики проверки (доступны менеджерам и выше)
    # =====================================================
    
    # Кнопка "Проверить" — начало процесса проверки
    bot.message_handler(
        func=lambda m: m.text == BTN_CHECK_USER,
        pass_bot=True
    )(require_role(Role.MANAGER, access_service)(check_user_handler))
    
    # Кнопка "Отменить проверку"
    @bot.message_handler(
        func=lambda m: m.text == BTN_CANCEL_CHECK,
        pass_bot=True
    )
    async def _cancel_check_wrapper(message, bot):
        user_id = message.from_user.id
        if await user_state_storage.is_checking(user_id):
            await check_message_handler(message, bot, context)
    
    # =====================================================
    # Callback-обработчики
    # =====================================================
    
    # Callback для добавления в ЧС (подтверждение и выбор причины)
    @bot.callback_query_handler(
        func=lambda call: (
            call.data in [CALLBACK_CONFIRM_ADD, CALLBACK_EDIT, CALLBACK_CANCEL]
            or call.data.startswith(CALLBACK_REASON_PREFIX)
        )
    )
    async def _blacklist_callback_wrapper(call):
        await blacklist_callback_handler(call, bot)
    
    # Callback для проверки в ЧС
    @bot.callback_query_handler(
        func=lambda call: call.data in [
            CALLBACK_CHECK_CONFIRM,
            CALLBACK_CHECK_EDIT,
            CALLBACK_CHECK_CANCEL
        ]
    )
    async def _check_callback_wrapper(call):
        await check_callback_handler(call, bot, context)
    
    # =====================================================
    # Общий обработчик сообщений (должен быть последним!)
    # =====================================================
    @bot.message_handler(
        func=lambda m: True,  # Фильтрация происходит внутри
        pass_bot=True
    )
    async def _message_wrapper(message, bot):
        user_id = message.from_user.id
        
        # Проверяем состояние пользователя
        if await user_state_storage.is_adding(user_id):
            # Пользователь в процессе добавления в ЧС
            await blacklist_message_handler(message, bot)
        elif await user_state_storage.is_checking(user_id):
            # Пользователь в процессе проверки
            await check_message_handler(message, bot, context)
    
    logger.info("Обработчики бота зарегистрированы")