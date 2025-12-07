"""
Клавиатуры для главного меню бота.
"""
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# Константы текстов кнопок
BTN_ADD_TO_BLACKLIST = "Добавить в ЧС"
BTN_CHECK_USER = "Проверить"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создать клавиатуру главного меню.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Первый ряд - две кнопки
    keyboard.add(
        KeyboardButton(BTN_ADD_TO_BLACKLIST),
        KeyboardButton(BTN_CHECK_USER),
    )
    
    return keyboard

