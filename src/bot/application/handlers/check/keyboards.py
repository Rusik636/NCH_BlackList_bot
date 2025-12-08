"""
Клавиатуры для процесса проверки в черном списке.
"""
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# Константы текстов кнопок
BTN_CANCEL_CHECK = "❌ Отменить проверку"

# Callback data для инлайн-кнопок
CALLBACK_CHECK_CONFIRM = "check_confirm"
CALLBACK_CHECK_EDIT = "check_edit"
CALLBACK_CHECK_CANCEL = "check_cancel"


def get_cancel_check_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены проверки.
    
    Returns:
        ReplyKeyboardMarkup с кнопкой "Отменить проверку"
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(BTN_CANCEL_CHECK))
    return keyboard


def get_check_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура для подтверждения данных поиска.
    
    Returns:
        InlineKeyboardMarkup с кнопками "Проверить", "Изменить", "Отмена"
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🔍 Проверить", callback_data=CALLBACK_CHECK_CONFIRM),
        InlineKeyboardButton("✏️ Изменить", callback_data=CALLBACK_CHECK_EDIT),
        InlineKeyboardButton("❌ Отмена", callback_data=CALLBACK_CHECK_CANCEL),
    )
    return keyboard

