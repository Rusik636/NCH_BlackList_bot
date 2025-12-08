"""
Обработчик добавления в черный список.
Пошаговый сбор данных с удалением сообщений пользователя.
"""
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery

from src.bot.application.states import BlacklistAddState
from src.bot.application.storage import user_state_storage, BlacklistCollectionData
from src.bot.application.context import get_bot_context
from src.bot.application.keyboard import get_main_menu_keyboard
from src.bot.application.handlers.blacklist.keyboards import (
    get_cancel_keyboard,
    get_skip_keyboard,
    get_confirmation_keyboard,
    get_reasons_keyboard,
    BTN_CANCEL_PROCESS,
    BTN_SKIP,
    CALLBACK_CONFIRM_ADD,
    CALLBACK_EDIT,
    CALLBACK_CANCEL,
    CALLBACK_REASON_PREFIX,
    POPULAR_REASONS,
)
from src.bot.utils import Validators
from src.bot.service.hash_service import PersonalData

logger = logging.getLogger(__name__)


# Сообщения для каждого шага
STEP_MESSAGES = {
    BlacklistAddState.WAITING_FIO: (
        "📝 <b>Шаг 1/7: ФИО</b>\n\n"
        "Введите ФИО арендатора:\n"
        "<i>Формат: Фамилия Имя Отчество</i>"
    ),
    BlacklistAddState.WAITING_BIRTHDATE: (
        "📅 <b>Шаг 2/7: Дата рождения</b>\n\n"
        "Введите дату рождения:\n"
        "<i>Формат: ДД.ММ.ГГГГ</i>"
    ),
    BlacklistAddState.WAITING_PASSPORT: (
        "🪪 <b>Шаг 3/7: Паспортные данные</b>\n\n"
        "Введите серию и номер паспорта:\n"
        "<i>Формат: 1234 567890 или 1234567890</i>"
    ),
    BlacklistAddState.WAITING_DEPARTMENT_CODE: (
        "🏢 <b>Шаг 4/7: Код подразделения</b>\n\n"
        "Введите код подразделения:\n"
        "<i>Формат: 123-456 или 123456 (6 цифр)</i>"
    ),
    BlacklistAddState.WAITING_PHONE: (
        "📱 <b>Шаг 5/7: Номер телефона</b>\n\n"
        "Введите номер телефона (если известен):\n"
        "<i>Формат: +79991234567</i>\n\n"
        "Или нажмите «Пропустить», если номер неизвестен."
    ),
    BlacklistAddState.WAITING_REASON: (
        "📋 <b>Шаг 6/7: Причина</b>\n\n"
        "Укажите причину добавления в черный список:"
    ),
    BlacklistAddState.WAITING_COMMENT: (
        "💬 <b>Шаг 7/7: Комментарий</b>\n\n"
        "Добавьте комментарий (дополнительная информация):\n\n"
        "Или нажмите «Пропустить», если комментарий не требуется."
    ),
}


async def _delete_message_safe(
    bot: AsyncTeleBot, 
    chat_id: int, 
    message_id: int
) -> None:
    """
    Безопасное удаление сообщения (игнорирует ошибки).
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        message_id: ID сообщения
    """
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")


async def _delete_bot_messages(bot: AsyncTeleBot, chat_id: int, user_id: int) -> None:
    """
    Удаляет все отслеживаемые сообщения бота для пользователя.
    """
    message_ids = await user_state_storage.clear_bot_messages(user_id)
    for msg_id in message_ids:
        await _delete_message_safe(bot, chat_id, msg_id)


async def _send_step_message(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    state: BlacklistAddState,
) -> None:
    """
    Отправить сообщение для текущего шага.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        user_id: ID пользователя
        state: Текущее состояние
    """
    message_text = STEP_MESSAGES.get(state, "")
    
    # Для шага с причиной — отправляем инлайн-кнопки с популярными причинами
    if state == BlacklistAddState.WAITING_REASON:
        # Сначала отправляем reply-клавиатуру с кнопкой отмены
        step_message = await bot.send_message(
            chat_id,
            message_text,
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        # Отслеживаем первое сообщение
        await user_state_storage.add_bot_message(user_id, step_message.message_id)
        
        # Затем отправляем инлайн-клавиатуру с популярными причинами
        inline_message = await bot.send_message(
            chat_id,
            "👇 <b>Выберите причину или введите свою:</b>",
            parse_mode="HTML",
            reply_markup=get_reasons_keyboard(),
        )
        # Отслеживаем второе сообщение
        await user_state_storage.add_bot_message(user_id, inline_message.message_id)
        return
    
    # Выбираем клавиатуру в зависимости от шага
    # Для опциональных полей (телефон, комментарий) показываем кнопку "Пропустить"
    if state in (BlacklistAddState.WAITING_PHONE, BlacklistAddState.WAITING_COMMENT):
        keyboard = get_skip_keyboard()
    else:
        keyboard = get_cancel_keyboard()
    
    sent_message = await bot.send_message(
        chat_id,
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    
    await user_state_storage.set_last_bot_message(user_id, sent_message.message_id)


def _format_confirmation_message(
    data: BlacklistCollectionData
) -> str:
    """
    Сформировать сообщение для подтверждения данных.
    
    Args:
        data: Собранные данные
        
    Returns:
        Отформатированное сообщение
    """
    phone_display = data.phone if data.phone else "Не указан"
    comment_display = data.comment if data.comment else "Не указан"
    
    # Форматируем паспорт для отображения (XXXX XXXXXX)
    passport_display = data.passport
    if passport_display and len(passport_display) == 10:
        passport_display = f"{passport_display[:4]} {passport_display[4:]}"
    
    # Форматируем код подразделения (XXX-XXX)
    dept_display = data.department_code
    if dept_display and len(dept_display) == 6:
        dept_display = f"{dept_display[:3]}-{dept_display[3:]}"
    
    return (
        "📋 <b>Проверьте данные:</b>\n\n"
        f"👤 <b>ФИО:</b> {data.fio}\n"
        f"📅 <b>Дата рождения:</b> {data.birthdate}\n"
        f"🪪 <b>Паспорт:</b> {passport_display}\n"
        f"🏢 <b>Код подразделения:</b> {dept_display}\n"
        f"📱 <b>Телефон:</b> {phone_display}\n"
        f"📝 <b>Причина:</b> {data.reason}\n"
        f"💬 <b>Комментарий:</b> {comment_display}\n\n"
        "Выберите действие:"
    )


async def add_to_blacklist_handler(
    message: Message, 
    bot: AsyncTeleBot
) -> None:
    """
    Обработчик нажатия кнопки "Добавить в ЧС".
    Начинает процесс сбора данных.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    logger.info(f"Пользователь {user_id} начал добавление в ЧС")
    
    # Очищаем предыдущее состояние, если было
    await user_state_storage.clear(user_id)
    
    # Устанавливаем начальное состояние
    await user_state_storage.set_state(user_id, BlacklistAddState.WAITING_FIO)
    
    # Отправляем первый шаг
    await _send_step_message(bot, chat_id, user_id, BlacklistAddState.WAITING_FIO)


async def cancel_collection_handler(
    message: Message, 
    bot: AsyncTeleBot
) -> None:
    """
    Обработчик кнопки "Прервать процесс".
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Удаляем сообщение пользователя
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Удаляем последнее сообщение бота
    last_msg_id = await user_state_storage.get_last_bot_message(user_id)
    if last_msg_id:
        await _delete_message_safe(bot, chat_id, last_msg_id)
    
    # Очищаем состояние
    await user_state_storage.clear(user_id)
    
    # Отправляем сообщение об отмене с меню
    await bot.send_message(
        chat_id,
        "❌ Процесс добавления в ЧС прерван.",
        reply_markup=get_main_menu_keyboard(),
    )
    
    logger.info(f"Пользователь {user_id} прервал добавление в ЧС")


async def blacklist_message_handler(
    message: Message, 
    bot: AsyncTeleBot
) -> None:
    """
    Обработчик сообщений во время сбора данных для черного списка.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Игнорируем нетекстовые сообщения (фото, стикеры и т.д.)
    if message.text is None:
        return
    
    text = message.text.strip()
    
    # Получаем текущее состояние
    state = await user_state_storage.get_state(user_id)
    
    if not state:
        return
    
    # Удаляем сообщение пользователя (защита персональных данных)
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Удаляем предыдущее сообщение бота
    last_msg_id = await user_state_storage.get_last_bot_message(user_id)
    if last_msg_id:
        await _delete_message_safe(bot, chat_id, last_msg_id)
    
    # Обработка в зависимости от состояния
    next_state = None
    error_message = None
    
    if state == BlacklistAddState.WAITING_FIO:
        result = Validators.validate_fio(text)
        if result.is_valid:
            await user_state_storage.update_data(user_id, fio=result.normalized)
            next_state = BlacklistAddState.WAITING_BIRTHDATE
        else:
            error_message = result.error
            next_state = state
    
    elif state == BlacklistAddState.WAITING_BIRTHDATE:
        result = Validators.validate_birthdate(text)
        if result.is_valid:
            await user_state_storage.update_data(user_id, birthdate=result.normalized)
            next_state = BlacklistAddState.WAITING_PASSPORT
        else:
            error_message = result.error
            next_state = state
    
    elif state == BlacklistAddState.WAITING_PASSPORT:
        result = Validators.validate_passport(text)
        if result.is_valid:
            await user_state_storage.update_data(user_id, passport=result.normalized)
            next_state = BlacklistAddState.WAITING_DEPARTMENT_CODE
        else:
            error_message = result.error
            next_state = state
    
    elif state == BlacklistAddState.WAITING_DEPARTMENT_CODE:
        result = Validators.validate_department_code(text)
        if result.is_valid:
            await user_state_storage.update_data(user_id, department_code=result.normalized)
            next_state = BlacklistAddState.WAITING_PHONE
        else:
            error_message = result.error
            next_state = state
    
    elif state == BlacklistAddState.WAITING_PHONE:
        if text == BTN_SKIP:
            # Пропуск телефона
            await user_state_storage.update_data(user_id, phone=None)
            next_state = BlacklistAddState.WAITING_REASON
        else:
            result = Validators.validate_phone(text)
            if result.is_valid:
                await user_state_storage.update_data(user_id, phone=result.normalized)
                next_state = BlacklistAddState.WAITING_REASON
            else:
                error_message = result.error
                next_state = state
    
    elif state == BlacklistAddState.WAITING_REASON:
        result = Validators.validate_reason(text)
        if result.is_valid:
            await user_state_storage.update_data(user_id, reason=result.normalized)
            next_state = BlacklistAddState.WAITING_COMMENT
        else:
            error_message = result.error
            next_state = state
    
    elif state == BlacklistAddState.WAITING_COMMENT:
        if text == BTN_SKIP:
            # Пропуск комментария
            await user_state_storage.update_data(user_id, comment=None)
            next_state = BlacklistAddState.CONFIRMATION
        else:
            # Комментарий без строгой валидации, только ограничение длины
            if len(text) > 1000:
                error_message = "Комментарий не должен превышать 1000 символов"
                next_state = state
            else:
                await user_state_storage.update_data(user_id, comment=text)
                next_state = BlacklistAddState.CONFIRMATION
    
    # Устанавливаем следующее состояние
    await user_state_storage.set_state(user_id, next_state)
    
    # Отправляем следующее сообщение
    if next_state == BlacklistAddState.CONFIRMATION:
        # Показываем данные для подтверждения
        data = await user_state_storage.get_data(user_id)
        confirmation_text = _format_confirmation_message(data)
        
        sent_message = await bot.send_message(
            chat_id,
            confirmation_text,
            parse_mode="HTML",
            reply_markup=get_confirmation_keyboard(),
        )
        await user_state_storage.set_last_bot_message(user_id, sent_message.message_id)
    else:
        # Если была ошибка, добавляем её к сообщению шага
        if error_message:
            step_text = STEP_MESSAGES.get(next_state, "")
            full_text = f"⚠️ <b>{error_message}</b>\n\n{step_text}"
            
            # Для опциональных полей показываем кнопку "Пропустить"
            if next_state in (BlacklistAddState.WAITING_PHONE, BlacklistAddState.WAITING_COMMENT):
                keyboard = get_skip_keyboard()
            else:
                keyboard = get_cancel_keyboard()
            
            sent_message = await bot.send_message(
                chat_id,
                full_text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            await user_state_storage.set_last_bot_message(user_id, sent_message.message_id)
        else:
            await _send_step_message(bot, chat_id, user_id, next_state)


async def blacklist_callback_handler(
    call: CallbackQuery, 
    bot: AsyncTeleBot
) -> None:
    """
    Обработчик инлайн-кнопок (подтверждение и выбор причины).
    
    Args:
        call: Callback query
        bot: Экземпляр бота
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    callback_data = call.data
    
    # Подтверждаем получение callback
    await bot.answer_callback_query(call.id)
    
    # Обработка выбора причины из списка
    if callback_data.startswith(CALLBACK_REASON_PREFIX):
        reason_index = int(callback_data.replace(CALLBACK_REASON_PREFIX, ""))
        
        if 0 <= reason_index < len(POPULAR_REASONS):
            selected_reason = POPULAR_REASONS[reason_index]
            
            # Удаляем все сообщения бота (включая шаг и инлайн-кнопки)
            await _delete_bot_messages(bot, chat_id, user_id)
            
            # Сохраняем причину
            await user_state_storage.update_data(user_id, reason=selected_reason)
            
            # Переходим к следующему шагу
            await user_state_storage.set_state(user_id, BlacklistAddState.WAITING_COMMENT)
            await _send_step_message(bot, chat_id, user_id, BlacklistAddState.WAITING_COMMENT)
            
            logger.debug(f"Пользователь {user_id} выбрал причину: {selected_reason}")
        return
    
    if callback_data == CALLBACK_CONFIRM_ADD:
        # Удаляем сообщение подтверждения
        await _delete_message_safe(bot, chat_id, message_id)
        
        # Получаем данные
        data = await user_state_storage.get_data(user_id)
        
        # Получаем контекст и сервисы
        context = get_bot_context()
        
        # Получаем admin из БД по telegram_id
        admin = await context.admin_repository.get_by_admin_id(user_id)
        if not admin:
            await bot.send_message(
                chat_id,
                "❌ Ошибка: администратор не найден в системе.",
                reply_markup=get_main_menu_keyboard(),
            )
            await user_state_storage.clear(user_id)
            return
        
        # Получаем организации админа
        admin_orgs = await context.db_manager.fetch(
            """
            SELECT o.id, o.name, o.hash_salt 
            FROM organizations o
            JOIN admin_organizations ao ON o.id = ao.organization_id
            WHERE ao.admin_id = $1
            """,
            admin.id
        )
        
        if not admin_orgs:
            await bot.send_message(
                chat_id,
                "❌ Ошибка: у вас нет привязанных организаций.",
                reply_markup=get_main_menu_keyboard(),
            )
            await user_state_storage.clear(user_id)
            return
        
        # Используем первую организацию (TODO: добавить выбор организации)
        org = admin_orgs[0]
        
        # Разбираем ФИО на части
        fio_parts = data.fio.split() if data.fio else []
        surname = fio_parts[0] if len(fio_parts) > 0 else ""
        name = fio_parts[1] if len(fio_parts) > 1 else ""
        patronymic = " ".join(fio_parts[2:]) if len(fio_parts) > 2 else ""
        
        # Создаём PersonalData для хеширования
        personal_data = PersonalData(
            surname=surname,
            name=name,
            patronymic=patronymic,
            birthdate=data.birthdate or "",
            passport=data.passport or "",
            department_code=data.department_code or "",
            phone=data.phone or "",
        )
        
        # Добавляем в черный список через сервис
        result = await context.blacklist_service.add_to_blacklist(
            organization_id=org["id"],
            admin_id=admin.id,
            personal_data=personal_data,
            reason=data.reason or "Не указана",
            comment=data.comment,
        )
        
        # Очищаем состояние
        await user_state_storage.clear(user_id)
        
        if result.success:
            status_text = "⚠️ (повторное добавление)" if result.already_exists else ""
            await bot.send_message(
                chat_id,
                f"✅ Запись успешно добавлена в черный список! {status_text}",
                reply_markup=get_main_menu_keyboard(),
            )
            logger.info(f"Пользователь {user_id} добавил запись в ЧС: {data.fio}")
        else:
            await bot.send_message(
                chat_id,
                f"❌ Ошибка при добавлении: {result.error}",
                reply_markup=get_main_menu_keyboard(),
            )
            logger.error(f"Ошибка при добавлении в ЧС пользователем {user_id}: {result.error}")
    
    elif callback_data == CALLBACK_EDIT:
        # Удаляем сообщение подтверждения
        await _delete_message_safe(bot, chat_id, message_id)
        
        # Сбрасываем данные, но не состояние
        await user_state_storage.reset_data(user_id)
        
        # Начинаем сбор заново
        await user_state_storage.set_state(user_id, BlacklistAddState.WAITING_FIO)
        await _send_step_message(bot, chat_id, user_id, BlacklistAddState.WAITING_FIO)
        
        logger.info(f"Пользователь {user_id} начал редактирование данных ЧС")
    
    elif callback_data == CALLBACK_CANCEL:
        # Удаляем сообщение подтверждения
        await _delete_message_safe(bot, chat_id, message_id)
        
        # Очищаем состояние
        await user_state_storage.clear(user_id)
        
        await bot.send_message(
            chat_id,
            "❌ Добавление в ЧС отменено.",
            reply_markup=get_main_menu_keyboard(),
        )
        
        logger.info(f"Пользователь {user_id} отменил добавление в ЧС")