"""
Состояния FSM для проверки пользователя в черном списке.
"""
from enum import Enum, auto


class CheckState(Enum):
    """Состояния процесса проверки в черном списке."""
    
    # Ожидание ввода данных для поиска
    WAITING_INPUT = auto()
    
    # Подтверждение данных перед поиском
    CONFIRMATION = auto()
    
    # Отображение результатов поиска
    SHOWING_RESULTS = auto()

