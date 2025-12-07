"""
Состояния FSM для сбора данных при добавлении в черный список.
"""
from enum import Enum, auto


class BlacklistAddState(Enum):
    """Состояния процесса добавления в черный список."""
    
    # Ожидание ввода ФИО
    WAITING_FIO = auto()
    
    # Ожидание ввода даты рождения
    WAITING_BIRTHDATE = auto()
    
    # Ожидание ввода паспортных данных (серия и номер)
    WAITING_PASSPORT = auto()
    
    # Ожидание ввода кода подразделения
    WAITING_DEPARTMENT_CODE = auto()
    
    # Ожидание ввода номера телефона
    WAITING_PHONE = auto()
    
    # Ожидание ввода причины добавления в ЧС
    WAITING_REASON = auto()
    
    # Подтверждение данных
    CONFIRMATION = auto()

