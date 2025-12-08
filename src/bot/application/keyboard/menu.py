"""
Клавиатуры для главного меню бота.
"""
from typing import Optional

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from src.bot.domain.role import Role


# Константы текстов кнопок
BTN_ADD_TO_BLACKLIST = "Добавить в ЧС"
BTN_CHECK_USER = "Проверить"
BTN_EDIT_BLACKLIST = "Редактировать ЧС"


def get_main_menu_keyboard(user_role: Optional[Role] = None) -> ReplyKeyboardMarkup:
    """
    Создать клавиатуру главного меню с учетом прав доступа пользователя.
    
    Args:
        user_role: Роль пользователя. Если None, показываются все кнопки (для обратной совместимости)
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = []
    
    # Кнопка "Добавить в ЧС" - только для админов и выше
    if user_role is None or Role.has_access(user_role, Role.ADMIN):
        buttons.append(KeyboardButton(BTN_ADD_TO_BLACKLIST))
    
    # Кнопка "Проверить" - для менеджеров и выше
    if user_role is None or Role.has_access(user_role, Role.MANAGER):
        buttons.append(KeyboardButton(BTN_CHECK_USER))
    
    # Кнопка "Редактировать ЧС" - только для админов и выше
    if user_role is None or Role.has_access(user_role, Role.ADMIN):
        buttons.append(KeyboardButton(BTN_EDIT_BLACKLIST))
    
    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.add(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])
    
    return keyboard

