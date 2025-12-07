"""
Клавиатуры для главного меню бота.
"""
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# Константы текстов кнопок
BTN_ADD_TO_BLACKLIST = "Добавить в ЧС"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создать клавиатуру главного меню.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Первая кнопка - Добавить в ЧС
    keyboard.add(KeyboardButton(BTN_ADD_TO_BLACKLIST))
    
    return keyboard

