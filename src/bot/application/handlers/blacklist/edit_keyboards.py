"""
Клавиатуры для редактора записей черного списка.
"""
from typing import List, Dict
from uuid import UUID

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# Callback префиксы
CALLBACK_EDIT_RECORD_PREFIX = "edit_record_"
CALLBACK_TOGGLE_STATUS = "toggle_status"
CALLBACK_EDIT_BACK = "edit_back"
CALLBACK_EDIT_FINISH = "edit_finish"
CALLBACK_EDIT_CANCEL = "edit_cancel"


def get_record_selection_keyboard(records: List[Dict]) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора записи из списка найденных.
    
    Args:
        records: Список найденных записей с полем 'record_id'
    
    Returns:
        InlineKeyboardMarkup с кнопками для каждой записи и кнопкой "Отменить"
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for i, record in enumerate(records, 1):
        record_id = record.get('record_id', '')
        record_id_short = record_id[-6:] if record_id else 'N/A'
        button_text = f"Запись #{i} (ID: {record_id_short})"
        callback_data = f"{CALLBACK_EDIT_RECORD_PREFIX}{record_id}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data=CALLBACK_EDIT_CANCEL))
    
    return keyboard


def get_record_edit_keyboard(record_id: UUID, is_active: bool) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для редактирования записи.
    
    Args:
        record_id: UUID записи
        is_active: True если запись активна, False если неактивна
    
    Returns:
        InlineKeyboardMarkup с кнопками управления записью
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка переключения статуса (меняется в зависимости от текущего статуса)
    if is_active:
        keyboard.add(InlineKeyboardButton("🔴 Снять ЧС", callback_data=CALLBACK_TOGGLE_STATUS))
    else:
        keyboard.add(InlineKeyboardButton("🟢 Вернуть в ЧС", callback_data=CALLBACK_TOGGLE_STATUS))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data=CALLBACK_EDIT_BACK))
    keyboard.add(InlineKeyboardButton("✅ Завершить", callback_data=CALLBACK_EDIT_FINISH))
    
    return keyboard

