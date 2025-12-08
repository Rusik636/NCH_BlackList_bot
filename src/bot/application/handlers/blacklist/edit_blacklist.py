"""
Обработчик редактирования записей черного списка.
"""
import logging
from typing import List, Optional
from uuid import UUID

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery

from src.bot.application.keyboard import get_main_menu_keyboard
from src.bot.application.context import get_bot_context
from src.bot.application.states import EditState
from src.bot.application.storage import user_state_storage, CheckSearchData, EditData
from src.bot.application.handlers.check.keyboards import get_cancel_check_keyboard, BTN_CANCEL_CHECK
from src.bot.application.handlers.blacklist.edit_keyboards import (
    get_record_selection_keyboard,
    get_record_edit_keyboard,
    CALLBACK_EDIT_RECORD_PREFIX,
    CALLBACK_TOGGLE_STATUS,
    CALLBACK_EDIT_BACK,
    CALLBACK_EDIT_FINISH,
    CALLBACK_EDIT_CANCEL,
)
from src.bot.utils import SearchDataParser
from src.bot.domain.blacklist_record import BlacklistStatus

logger = logging.getLogger(__name__)


# Сообщение с просьбой ввести данные
INPUT_MESSAGE = """
🔧 <b>Редактирование черного списка</b>

Введите ID записи (последние 6 символов) или данные для поиска:

• <b>ID записи</b> — последние 6 символов (например: abc123)
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


def _format_record_details(record: dict) -> str:
    """Форматирует детали одной записи для отображения."""
    record_id = record.get('record_id', '')
    record_id_short = record_id[-6:] if record_id else 'N/A'
    
    lines = [f"━━━━━ Запись (ID: <code>{record_id_short}</code>) ━━━━━"]
    
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
        lines.append(f"💬 <b>Комментарий:</b>\n<blockquote>{comment}</blockquote>")
    
    matched = record.get('matched_fields', [])
    if matched:
        lines.append(f"🔗 <b>Совпадение по:</b> {', '.join(matched)}")
    
    return "\n".join(lines)


def _format_search_results(results: List[dict]) -> str:
    """Форматирует результаты поиска для отображения."""
    if not results:
        return (
            "🔍 <b>Результат поиска</b>\n\n"
            "❌ <b>Записи не найдены.</b>"
        )
    
    lines = [f"🚫 <b>Найдено записей: {len(results)}</b>\n"]
    
    for i, record in enumerate(results, 1):
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
            lines.append(f"💬 <b>Комментарий:</b>\n<blockquote>{comment}</blockquote>")
        
        matched = record.get('matched_fields', [])
        if matched:
            lines.append(f"🔗 <b>Совпадение по:</b> {', '.join(matched)}")
        
        lines.append("")
    
    return "\n".join(lines)


async def _search_by_record_id(
    context, 
    record_id_short: str, 
    organization_ids: List[int]
) -> Optional[dict]:
    """
    Поиск записи по последним 6 символам ID с фильтрацией по организациям.
    
    Args:
        context: BotContext
        record_id_short: Последние 6 символов ID записи
        organization_ids: Список ID организаций для фильтрации
    
    Returns:
        Словарь с данными записи или None
    """
    if not organization_ids:
        return None
    
    try:
        # Ищем все записи, у которых ID заканчивается на указанные символы
        # и которые принадлежат указанным организациям
        query = """
            SELECT br.*, o.name as organization_name, a.admin_id as admin_telegram_id
            FROM blacklist_records br
            JOIN organizations o ON br.organization_id = o.id
            JOIN admins a ON br.added_by_admin_id = a.id
            WHERE br.id::text LIKE $1
              AND br.organization_id = ANY($2::int[])
            ORDER BY br.created DESC
            LIMIT 10
        """
        pattern = f"%{record_id_short}"
        rows = await context.db_manager.fetch(query, pattern, organization_ids)
        
        if not rows:
            return None
        
        # Берем первую запись (самую новую)
        row = rows[0]
        
        # Форматируем как результат поиска
        return {
            'record_id': str(row['id']),
            'organization_id': row['organization_id'],
            'organization_name': row['organization_name'],
            'admin_telegram_id': row['admin_telegram_id'],
            'created': row['created'].strftime('%d.%m.%Y %H:%M'),
            'reason': row['reason'],
            'comment': row.get('comment'),
            'status': row['status'],
            'matched_fields': ['ID записи'],
        }
    except Exception as e:
        logger.error(f"Ошибка при поиске по ID записи {record_id_short}: {e}", exc_info=True)
        return None


async def edit_blacklist_handler(message: Message, bot: AsyncTeleBot) -> None:
    """
    Обработчик кнопки "Редактировать ЧС".
    Начинает процесс редактирования.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    logger.info(f"Пользователь {user_id} начал редактирование ЧС")
    
    # Удаляем сообщение с кнопкой меню
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Очищаем предыдущее состояние
    await user_state_storage.clear(user_id)
    
    # Устанавливаем состояние ожидания ввода
    await user_state_storage.set_state(user_id, EditState.WAITING_INPUT)
    
    # Отправляем сообщение с инструкцией
    sent_message = await bot.send_message(
        chat_id,
        INPUT_MESSAGE,
        parse_mode="HTML",
        reply_markup=get_cancel_check_keyboard(),  # Используем ту же клавиатуру отмены
    )
    
    await user_state_storage.add_bot_message(user_id, sent_message.message_id)


async def edit_message_handler(message: Message, bot: AsyncTeleBot, context) -> None:
    """
    Обработчик сообщений во время процесса редактирования.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Игнорируем нетекстовые сообщения
    if message.text is None:
        return
    
    text = message.text.strip()
    
    # Проверяем текущее состояние
    state = await user_state_storage.get_state(user_id)
    
    if not isinstance(state, EditState):
        return
    
    # Обработка кнопки отмены
    if text == BTN_CANCEL_CHECK:
        await _delete_message_safe(bot, chat_id, message.message_id)
        await _delete_bot_messages(bot, chat_id, user_id)
        await user_state_storage.clear(user_id)
        
        # Получаем роль пользователя для отображения соответствующей клавиатуры
        user_role = await context.access_service.get_user_role(user_id)
        
        await bot.send_message(
            chat_id,
            "❌ Редактирование отменено.",
            reply_markup=get_main_menu_keyboard(user_role),
        )
        logger.info(f"Пользователь {user_id} отменил редактирование")
        return
    
    # Удаляем сообщение пользователя (содержит персональные данные)
    await _delete_message_safe(bot, chat_id, message.message_id)
    
    # Удаляем предыдущие сообщения бота
    await _delete_bot_messages(bot, chat_id, user_id)
    
    if state == EditState.WAITING_INPUT:
        # Получаем организации пользователя
        admin = await context.admin_repository.get_by_admin_id(user_id)
        if not admin:
            await bot.send_message(
                chat_id,
                "❌ Ошибка: администратор не найден в системе.",
                reply_markup=get_cancel_check_keyboard(),
            )
            return
        
        # Получаем ID организаций пользователя
        organization_ids = await context.organization_repository.get_organization_ids_by_admin_telegram_id(user_id)
        
        if not organization_ids:
            await bot.send_message(
                chat_id,
                "❌ Ошибка: у вас нет привязанных организаций.",
                reply_markup=get_cancel_check_keyboard(),
            )
            return
        
        results = []
        
        # Проверяем, является ли ввод ID записи (6 hex символов)
        if len(text) == 6 and all(c in '0123456789abcdefABCDEF' for c in text):
            # Пытаемся найти по ID (только записи своей организации)
            record = await _search_by_record_id(context, text, organization_ids)
            if record:
                results = [record]
        
        # Если не найдено по ID или ввод не похож на ID, ищем по данным
        if not results:
            # Парсим введенные данные
            parsed = SearchDataParser.parse(text)
            
            # Выполняем поиск по критериям с фильтрацией по организациям пользователя
            results = await context.blacklist_service.search_by_criteria_for_organizations(
                organization_ids=organization_ids,
                fio=parsed.fio,
                passport=parsed.passport,
                birthdate=parsed.birthdate,
                department_code=parsed.department_code,
                phone=parsed.phone,
            )
        
        if not results:
            # Записи не найдены
            sent_message = await bot.send_message(
                chat_id,
                "❌ Записи вашей организации не найдены. Попробуйте ввести другие данные.",
                parse_mode="HTML",
                reply_markup=get_cancel_check_keyboard(),
            )
            await user_state_storage.add_bot_message(user_id, sent_message.message_id)
            return
        
        # Сохраняем результаты
        edit_data = EditData(search_results=results)
        await user_state_storage.set_edit_data(user_id, edit_data)
        
        # Форматируем результаты
        result_text = _format_search_results(results)
        
        # Переходим к отображению результатов
        await user_state_storage.set_state(user_id, EditState.SHOWING_RESULTS)
        
        sent_message = await bot.send_message(
            chat_id,
            result_text,
            parse_mode="HTML",
            reply_markup=get_record_selection_keyboard(results),
        )
        
        # Сохраняем ID сообщения с результатами для кнопки "Назад"
        edit_data.last_message_id = sent_message.message_id
        await user_state_storage.set_edit_data(user_id, edit_data)
        
        await user_state_storage.add_bot_message(user_id, sent_message.message_id)


async def edit_callback_handler(call: CallbackQuery, bot: AsyncTeleBot, context) -> None:
    """
    Обработчик инлайн-кнопок для редактора.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    callback_data = call.data
    
    # Подтверждаем получение callback
    await bot.answer_callback_query(call.id)
    
    edit_data = await user_state_storage.get_edit_data(user_id)
    
    if callback_data.startswith(CALLBACK_EDIT_RECORD_PREFIX):
        # Выбор записи для редактирования
        record_id_str = callback_data.replace(CALLBACK_EDIT_RECORD_PREFIX, "")
        
        # Находим запись в результатах
        selected_record = None
        for record in edit_data.search_results:
            if record.get('record_id') == record_id_str:
                selected_record = record
                break
        
        if not selected_record:
            await bot.answer_callback_query(
                call.id,
                "❌ Запись не найдена!",
                show_alert=True
            )
            return
        
        # Проверяем, что запись принадлежит организации пользователя
        # Получаем организации пользователя
        organization_ids = await context.organization_repository.get_organization_ids_by_admin_telegram_id(user_id)
        
        if not organization_ids:
            await bot.answer_callback_query(
                call.id,
                "❌ У вас нет привязанных организаций!",
                show_alert=True
            )
            return
        
        # Получаем organization_id из записи
        record_org_id = selected_record.get('organization_id')
        
        # Если organization_id не указан в результатах, получаем его из БД
        if not record_org_id:
            record_obj = await context.blacklist_record_repository.get_by_id(UUID(record_id_str))
            if record_obj:
                record_org_id = record_obj.organization_id
            else:
                await bot.answer_callback_query(
                    call.id,
                    "❌ Запись не найдена в базе данных!",
                    show_alert=True
                )
                return
        
        # Проверяем принадлежность к организации пользователя
        if record_org_id not in organization_ids:
            await bot.answer_callback_query(
                call.id,
                "❌ У вас нет прав редактировать эту запись!",
                show_alert=True
            )
            logger.warning(
                f"Пользователь {user_id} попытался выбрать запись {record_id_str} "
                f"из чужой организации {record_org_id}"
            )
            return
        
        # Сохраняем выбранную запись
        edit_data.selected_record_id = record_id_str
        await user_state_storage.set_edit_data(user_id, edit_data)
        
        # Переходим к редактированию
        await user_state_storage.set_state(user_id, EditState.EDITING_RECORD)
        
        # Редактируем сообщение, оставляя только выбранную запись
        record_text = _format_record_details(selected_record)
        is_active = selected_record.get('status') == 'active'
        
        await bot.edit_message_text(
            record_text,
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_record_edit_keyboard(UUID(record_id_str), is_active),
        )
        
        logger.info(f"Пользователь {user_id} выбрал запись {record_id_str} для редактирования")
    
    elif callback_data == CALLBACK_TOGGLE_STATUS:
        # Переключение статуса записи
        if not edit_data.selected_record_id:
            await bot.answer_callback_query(
                call.id,
                "❌ Запись не выбрана!",
                show_alert=True
            )
            return
        
        record_id = UUID(edit_data.selected_record_id)
        
        # Получаем текущую запись
        record = await context.blacklist_record_repository.get_by_id(record_id)
        if not record:
            await bot.answer_callback_query(
                call.id,
                "❌ Запись не найдена!",
                show_alert=True
            )
            return
        
        # Получаем админа
        admin = await context.admin_repository.get_by_admin_id(user_id)
        if not admin:
            await bot.answer_callback_query(
                call.id,
                "❌ Администратор не найден!",
                show_alert=True
            )
            return
        
        # Проверяем, что запись принадлежит организации пользователя
        organization_ids = await context.organization_repository.get_organization_ids_by_admin_telegram_id(user_id)
        if record.organization_id not in organization_ids:
            await bot.answer_callback_query(
                call.id,
                "❌ У вас нет прав редактировать эту запись!",
                show_alert=True
            )
            logger.warning(
                f"Пользователь {user_id} попытался редактировать запись {record_id} "
                f"из чужой организации {record.organization_id}"
            )
            return
        
        # Переключаем статус
        if record.status == BlacklistStatus.ACTIVE:
            # Деактивируем
            updated_record = await context.blacklist_service.deactivate_record(
                record_id,
                admin.id,
            )
        else:
            # Активируем
            updated_record = await context.blacklist_service.reactivate_record(
                record_id,
                admin.id,
            )
        
        if not updated_record:
            await bot.answer_callback_query(
                call.id,
                "❌ Ошибка при изменении статуса!",
                show_alert=True
            )
            return
        
        # Находим запись в результатах для получения полных данных
        selected_record_dict = None
        for record in edit_data.search_results:
            if record.get('record_id') == edit_data.selected_record_id:
                selected_record_dict = record
                # Обновляем статус в результатах
                record['status'] = updated_record.status.value
                # Дата создания остается неизменной, не используем updated
                record['created'] = updated_record.created.strftime('%d.%m.%Y %H:%M')
                break
        
        if not selected_record_dict:
            await bot.answer_callback_query(
                call.id,
                "❌ Ошибка: запись не найдена в результатах!",
                show_alert=True
            )
            return
        
        await user_state_storage.set_edit_data(user_id, edit_data)
        
        # Обновляем сообщение с новой кнопкой
        record_dict = {
            'record_id': edit_data.selected_record_id,
            'status': updated_record.status.value,
            'organization_name': selected_record_dict.get('organization_name', 'Неизвестно'),
            'admin_telegram_id': selected_record_dict.get('admin_telegram_id', user_id),
            'created': updated_record.created.strftime('%d.%m.%Y %H:%M'),  # Используем дату создания, а не обновления
            'reason': updated_record.reason,
            'comment': updated_record.comment,
            'matched_fields': selected_record_dict.get('matched_fields', []),
        }
        
        record_text = _format_record_details(record_dict)
        is_active = updated_record.status == BlacklistStatus.ACTIVE
        
        await bot.edit_message_text(
            record_text,
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_record_edit_keyboard(record_id, is_active),
        )
        
        status_text = "активирована" if is_active else "деактивирована"
        await bot.answer_callback_query(
            call.id,
            f"✅ Запись {status_text}",
            show_alert=False
        )
        
        logger.info(f"Пользователь {user_id} {status_text} запись {record_id}")
    
    elif callback_data == CALLBACK_EDIT_BACK:
        # Возврат к списку записей
        if not edit_data.last_message_id:
            await bot.answer_callback_query(
                call.id,
                "❌ Нет предыдущего сообщения!",
                show_alert=True
            )
            return
        
        # Возвращаемся к состоянию показа результатов
        await user_state_storage.set_state(user_id, EditState.SHOWING_RESULTS)
        edit_data.selected_record_id = None
        await user_state_storage.set_edit_data(user_id, edit_data)
        
        # Форматируем результаты
        result_text = _format_search_results(edit_data.search_results)
        
        # Редактируем сообщение обратно к списку
        await bot.edit_message_text(
            result_text,
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_record_selection_keyboard(edit_data.search_results),
        )
        
        logger.info(f"Пользователь {user_id} вернулся к списку записей")
    
    elif callback_data == CALLBACK_EDIT_FINISH:
        # Завершение редактирования
        await _delete_message_safe(bot, chat_id, call.message.message_id)
        await user_state_storage.clear(user_id)
        
        # Получаем роль пользователя для отображения соответствующей клавиатуры
        user_role = await context.access_service.get_user_role(user_id)
        
        await bot.send_message(
            chat_id,
            "✅ Редактирование завершено.",
            reply_markup=get_main_menu_keyboard(user_role),
        )
        
        logger.info(f"Пользователь {user_id} завершил редактирование")
    
    elif callback_data == CALLBACK_EDIT_CANCEL:
        # Отмена редактирования
        await _delete_message_safe(bot, chat_id, call.message.message_id)
        await user_state_storage.clear(user_id)
        
        # Получаем роль пользователя для отображения соответствующей клавиатуры
        user_role = await context.access_service.get_user_role(user_id)
        
        await bot.send_message(
            chat_id,
            "❌ Редактирование отменено.",
            reply_markup=get_main_menu_keyboard(user_role),
        )
        
        logger.info(f"Пользователь {user_id} отменил редактирование")
