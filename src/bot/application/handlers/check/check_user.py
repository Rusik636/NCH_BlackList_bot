"""
Обработчик проверки пользователя в черном списке.
"""
import logging
from typing import Optional, List

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery

from src.bot.application.states import CheckState
from src.bot.application.storage import user_state_storage, CheckSearchData
from src.bot.application.keyboard import get_main_menu_keyboard
from src.bot.application.handlers.check.keyboards import (
    get_cancel_check_keyboard,
    get_check_confirmation_keyboard,
    BTN_CANCEL_CHECK,
    CALLBACK_CHECK_CONFIRM,
    CALLBACK_CHECK_EDIT,
    CALLBACK_CHECK_CANCEL,
)
from src.bot.utils import SearchDataParser
from src.bot.application.context import BotContext, get_bot_context

logger = logging.getLogger(__name__)


# Сообщение с просьбой ввести данные
INPUT_MESSAGE = """
🔍 <b>Проверка в черном списке</b>

Введите данные для поиска (каждый параметр с новой строки):

• <b>Паспорт</b> — серия и номер (10 цифр) ⭐
• <b>ФИО</b> — Фамилия Имя Отчество ⭐
• <b>Дата рождения</b> — ДД.ММ.ГГГГ
• <b>Код подразделения</b> — 6 цифр
• <b>Телефон</b> — +79991234567

<i>⭐ Обязательно укажите паспорт или ФИО + дополнительные данные.
Чем больше данных, тем точнее поиск.</i>

<b>Пример:</b>
<code>Иванов Иван Иванович
1234 567890
01.01.1990</code>
"""


async def _delete_message_safe(
    bot: AsyncTeleBot,
    chat_id: int,
    message_id: int
) -> None:
    """Безопасное удаление сообщения."""
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")


async def _delete_bot_messages(bot: AsyncTeleBot, chat_id: int, user_id: int) -> None:
    """Удаляет все отслеживаемые сообщения бота для пользователя."""
    message_ids = await user_state_storage.clear_bot_messages(user_id)
    for msg_id in message_ids:
        await _delete_message_safe(bot, chat_id, msg_id)


def _format_confirmation_message(check_data: CheckSearchData) -> str:
    """Форматирует сообщение с данными для подтверждения."""
    filled_fields = check_data.get_filled_fields()
    
    if not filled_fields:
        return "⚠️ Данные для проверки не распознаны."
    
    lines = ["📋 <b>Распознанные данные для проверки:</b>\n"]
    
    for field_name, field_value in filled_fields:
        lines.append(f"• <b>{field_name}:</b> {field_value}")
    
    lines.append("")
    
    if check_data.has_minimum_data():
        lines.append("✅ Достаточно данных для поиска.")
    else:
        lines.append("⚠️ <b>Недостаточно данных!</b> Нужно минимум 2 параметра.")
    
    lines.append("\nВыберите действие:")
    
    return "\n".join(lines)


def _format_search_results(
    results: List[dict],
    check_data: CheckSearchData
) -> str:
    """Форматирует результаты поиска для отображения."""
    if not results:
        # Форматируем данные поиска
        search_params = []
        for field_name, field_value in check_data.get_filled_fields():
            search_params.append(f"• {field_name}: {field_value}")
        
        return (
            "🔍 <b>Результат проверки</b>\n\n"
            f"<b>Данные для поиска:</b>\n" + "\n".join(search_params) + "\n\n"
            "✅ <b>Пользователь не найден в черном списке.</b>"
        )
    
    # Есть результаты
    lines = [
        f"🚫 <b>Найдено записей: {len(results)}</b>\n"
    ]
    
    for i, record in enumerate(results, 1):
        # Получаем последние 6 символов ID записи
        record_id = record.get('record_id', '')
        record_id_short = record_id[-6:] if record_id else 'N/A'
        lines.append(f"━━━━━ Запись #{i} (ID: <code>{record_id_short}</code>) ━━━━━")

        status = record.get('status', 'unknown')
        status_emoji = "🟢" if status == "active" else "🔴"
        status_text = "Активна" if status == "active" else "Неактивна"
        lines.append(f"{status_emoji} <b>Статус:</b> {status_text}")

        lines.append(f"🏢 <b>Организация:</b> {record.get('organization_name', 'Неизвестно')}")
        lines.append(f"👤 <b>Добавил:</b> ID {record.get('admin_telegram_id', 'Неизвестно')}\n")

        lines.append(f"📅 <b>Дата добавления:</b> {record.get('created', 'Неизвестно')}\n")

        lines.append(f"📝 <b>Причина:</b> {record.get('reason', 'Не указана')}")
        
        comment = record.get('comment')
        if comment:
            # Форматируем комментарий как цитату
            lines.append(f"💬 <b>Комментарий:</b>\n<blockquote>{comment}</blockquote>")
        
        # Совпавшие данные
        matched = record.get('matched_fields', [])
        if matched:
            lines.append(f"🔗 <b>Совпадение по:</b> {', '.join(matched)}")
        
        lines.append("")
    
    return "\n".join(lines)


async def check_user_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик нажатия кнопки "Проверить".
    Начинает процесс проверки в ЧС.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    logger.info(f"Пользователь {user_id} начал проверку в ЧС")
    
    # Удаляем сообщение с кнопкой меню
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Очищаем предыдущее состояние
    await user_state_storage.clear(user_id)
    
    # Устанавливаем состояние ожидания ввода
    await user_state_storage.set_state(user_id, CheckState.WAITING_INPUT)
    
    # Отправляем сообщение с инструкцией
    sent_message = await bot.send_message(
        chat_id,
        INPUT_MESSAGE,
        parse_mode="HTML",
        reply_markup=get_cancel_check_keyboard(),
    )
    
    await user_state_storage.add_bot_message(user_id, sent_message.message_id)


async def check_message_handler(message: Message, bot: AsyncTeleBot, context: BotContext) -> None:
    """
    Обработчик сообщений во время процесса проверки.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Проверяем текущее состояние
    state = await user_state_storage.get_state(user_id)
    
    if not isinstance(state, CheckState):
        return
    
    # Обработка кнопки отмены
    if text == BTN_CANCEL_CHECK:
        await _delete_message_safe(bot, chat_id, message.message_id)
        await _delete_bot_messages(bot, chat_id, user_id)
        await user_state_storage.clear(user_id)
        
        # Получаем роль пользователя для отображения соответствующей клавиатуры
        bot_context = get_bot_context()
        user_role = await bot_context.access_service.get_user_role(user_id)
        
        await bot.send_message(
            chat_id,
            "❌ Проверка отменена.",
            reply_markup=get_main_menu_keyboard(user_role),
        )
        logger.info(f"Пользователь {user_id} отменил проверку")
        return
    
    # Удаляем сообщение пользователя (содержит персональные данные)
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Удаляем предыдущие сообщения бота
    await _delete_bot_messages(bot, chat_id, user_id)
    
    if state == CheckState.WAITING_INPUT:
        # Парсим введенные данные
        parsed = SearchDataParser.parse(text)
        
        # Создаем CheckSearchData из распарсенных данных
        check_data = CheckSearchData(
            fio=parsed.fio,
            passport=parsed.passport,
            birthdate=parsed.birthdate,
            department_code=parsed.department_code,
            phone=parsed.phone,
            raw_input=text,
        )
        
        # Сохраняем данные
        await user_state_storage.set_check_data(user_id, check_data)
        
        # Формируем сообщение подтверждения
        confirmation_text = _format_confirmation_message(check_data)
        
        # Переходим к подтверждению
        await user_state_storage.set_state(user_id, CheckState.CONFIRMATION)
        
        sent_message = await bot.send_message(
            chat_id,
            confirmation_text,
            parse_mode="HTML",
            reply_markup=get_check_confirmation_keyboard(),
        )
        
        await user_state_storage.add_bot_message(user_id, sent_message.message_id)


async def check_callback_handler(call: CallbackQuery, bot: AsyncTeleBot, context: BotContext) -> None:
    """
    Обработчик инлайн-кнопок для проверки.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    callback_data = call.data
    
    # Подтверждаем получение callback
    await bot.answer_callback_query(call.id)
    
    if callback_data == CALLBACK_CHECK_CONFIRM:
        # Получаем данные для поиска
        check_data = await user_state_storage.get_check_data(user_id)
        
        if not check_data.has_minimum_data():
            await bot.answer_callback_query(
                call.id,
                "⚠️ Недостаточно данных для поиска!",
                show_alert=True
            )
            return
        
        # Удаляем сообщения бота
        await _delete_bot_messages(bot, chat_id, user_id)
        
        # Выполняем поиск
        try:
            results = await context.blacklist_service.search_by_criteria(
                fio=check_data.fio,
                passport=check_data.passport,
                birthdate=check_data.birthdate,
                department_code=check_data.department_code,
                phone=check_data.phone,
            )
            
            # Форматируем результаты
            result_text = _format_search_results(results, check_data)
            
            # Получаем роль пользователя для отображения соответствующей клавиатуры
            user_role = await context.access_service.get_user_role(user_id)
            
            await bot.send_message(
                chat_id,
                result_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(user_role),
            )
            
            logger.info(f"Пользователь {user_id} выполнил проверку, найдено: {len(results)}")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}", exc_info=True)
            
            # Получаем роль пользователя для отображения соответствующей клавиатуры
            user_role = await context.access_service.get_user_role(user_id)
            
            await bot.send_message(
                chat_id,
                "❌ Произошла ошибка при поиске. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user_role),
            )
        
        # Очищаем состояние
        await user_state_storage.clear(user_id)
    
    elif callback_data == CALLBACK_CHECK_EDIT:
        # Удаляем сообщения бота
        await _delete_bot_messages(bot, chat_id, user_id)
        
        # Сбрасываем данные проверки
        await user_state_storage.reset_check_data(user_id)
        
        # Возвращаемся к вводу
        await user_state_storage.set_state(user_id, CheckState.WAITING_INPUT)
        
        sent_message = await bot.send_message(
            chat_id,
            INPUT_MESSAGE,
            parse_mode="HTML",
            reply_markup=get_cancel_check_keyboard(),
        )
        
        await user_state_storage.add_bot_message(user_id, sent_message.message_id)
        
        logger.info(f"Пользователь {user_id} начал редактирование данных проверки")
    
    elif callback_data == CALLBACK_CHECK_CANCEL:
        # Удаляем сообщения бота
        await _delete_bot_messages(bot, chat_id, user_id)
        
        # Очищаем состояние
        await user_state_storage.clear(user_id)
        
        # Получаем роль пользователя для отображения соответствующей клавиатуры
        user_role = await context.access_service.get_user_role(user_id)
        
        await bot.send_message(
            chat_id,
            "❌ Проверка отменена.",
            reply_markup=get_main_menu_keyboard(user_role),
        )
        
        logger.info(f"Пользователь {user_id} отменил проверку через инлайн-кнопку")
