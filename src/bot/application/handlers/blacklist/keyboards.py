"""
Клавиатуры для процесса добавления в черный список.
"""
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# Константы текстов кнопок
BTN_CANCEL_PROCESS = "❌ Прервать процесс"
BTN_SKIP_PHONE = "Пропустить"

# Callback data для инлайн-кнопок
CALLBACK_CONFIRM_ADD = "blacklist_confirm_add"
CALLBACK_EDIT = "blacklist_edit"
CALLBACK_CANCEL = "blacklist_cancel"


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой прерывания процесса сбора данных.
    
    Returns:
        ReplyKeyboardMarkup с кнопкой "Прервать процесс"
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(BTN_CANCEL_PROCESS))
    return keyboard


def get_skip_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопками пропуска телефона и отмены.
    
    Returns:
        ReplyKeyboardMarkup с кнопками "Пропустить" и "Прервать процесс"
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton(BTN_SKIP_PHONE),
        KeyboardButton(BTN_CANCEL_PROCESS),
    )
    return keyboard


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура для подтверждения данных.
    
    Returns:
        InlineKeyboardMarkup с кнопками "Добавить", "Изменить", "Отменить"
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("✅ Добавить", callback_data=CALLBACK_CONFIRM_ADD),
        InlineKeyboardButton("✏️ Изменить", callback_data=CALLBACK_EDIT),
        InlineKeyboardButton("❌ Отменить", callback_data=CALLBACK_CANCEL),
    )
    return keyboard

