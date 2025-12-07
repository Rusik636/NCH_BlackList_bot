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
BTN_SKIP = "Пропустить"

# Для обратной совместимости
BTN_SKIP_PHONE = BTN_SKIP

# Callback data для инлайн-кнопок
CALLBACK_CONFIRM_ADD = "blacklist_confirm_add"
CALLBACK_EDIT = "blacklist_edit"
CALLBACK_CANCEL = "blacklist_cancel"
CALLBACK_REASON_PREFIX = "bl_reason_"

# Популярные причины добавления в ЧС (аренда электротранспорта)
POPULAR_REASONS = [
    "Невозврат транспорта",
    "Порча/поломка транспорта",
    "Долг по оплате аренды",
    "Нарушение ПДД",
    "Предоставление ложных данных",
]


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой прерывания процесса сбора данных.
    
    Returns:
        ReplyKeyboardMarkup с кнопкой "Прервать процесс"
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(BTN_CANCEL_PROCESS))
    return keyboard


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопками пропуска и отмены.
    Используется для опциональных полей (телефон, комментарий).
    
    Returns:
        ReplyKeyboardMarkup с кнопками "Пропустить" и "Прервать процесс"
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton(BTN_SKIP),
        KeyboardButton(BTN_CANCEL_PROCESS),
    )
    return keyboard


# Для обратной совместимости
def get_skip_phone_keyboard() -> ReplyKeyboardMarkup:
    """Алиас для get_skip_keyboard()."""
    return get_skip_keyboard()


def get_reasons_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура с популярными причинами добавления в ЧС.
    
    Returns:
        InlineKeyboardMarkup с кнопками причин
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for i, reason in enumerate(POPULAR_REASONS):
        # Сокращаем текст кнопки если слишком длинный
        button_text = reason if len(reason) <= 30 else reason[:27] + "..."
        keyboard.add(
            InlineKeyboardButton(
                f"📌 {button_text}",
                callback_data=f"{CALLBACK_REASON_PREFIX}{i}"
            )
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

