"""
Состояния FSM для редактора записей черного списка.
"""
from enum import Enum


class EditState(str, Enum):
    """Состояния процесса редактирования записей ЧС."""
    
    WAITING_INPUT = "waiting_input"  # Ожидание ввода ID или данных для поиска
    SHOWING_RESULTS = "showing_results"  # Отображение найденных записей
    EDITING_RECORD = "editing_record"  # Редактирование конкретной записи

