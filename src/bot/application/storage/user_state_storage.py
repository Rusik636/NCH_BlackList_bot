"""
Хранилище состояний пользователей.
Потокобезопасное хранение данных сбора для каждого пользователя.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.bot.application.states.blacklist_states import BlacklistAddState
from src.bot.application.states.check_states import CheckState

logger = logging.getLogger(__name__)


# Типы состояний FSM
StateType = Union[BlacklistAddState, CheckState, None]


@dataclass
class BlacklistCollectionData:
    """
    Данные, собранные в процессе добавления в черный список.
    
    Attributes:
        fio: ФИО (Фамилия Имя Отчество)
        birthdate: Дата рождения
        passport: Серия и номер паспорта
        department_code: Код подразделения
        phone: Номер телефона (опционально)
        reason: Причина добавления в ЧС
        comment: Дополнительный комментарий (опционально)
        started_at: Время начала сбора данных
    """
    fio: Optional[str] = None
    birthdate: Optional[str] = None
    passport: Optional[str] = None
    department_code: Optional[str] = None
    phone: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)


@dataclass
class CheckSearchData:
    """
    Данные для поиска в черном списке.
    
    Attributes:
        fio: ФИО (распознанное из текста)
        birthdate: Дата рождения (распознанная)
        passport: Серия и номер паспорта (распознанный)
        department_code: Код подразделения (распознанный)
        phone: Номер телефона (распознанный)
        raw_input: Исходный текст пользователя
        started_at: Время начала поиска
    """
    fio: Optional[str] = None
    birthdate: Optional[str] = None
    passport: Optional[str] = None
    department_code: Optional[str] = None
    phone: Optional[str] = None
    raw_input: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    
    def has_minimum_data(self) -> bool:
        """Проверяет, есть ли минимум данных для поиска (2 признака)."""
        filled_fields = sum([
            bool(self.passport),
            bool(self.department_code),
            bool(self.birthdate),
            bool(self.phone),
            bool(self.fio),
        ])
        return filled_fields >= 2
    
    def get_filled_fields(self) -> list:
        """Возвращает список заполненных полей."""
        fields = []
        if self.fio:
            fields.append(("ФИО", self.fio))
        if self.passport:
            # Форматируем паспорт для отображения
            passport_display = self.passport
            if len(self.passport) == 10:
                passport_display = f"{self.passport[:4]} {self.passport[4:]}"
            fields.append(("Паспорт", passport_display))
        if self.birthdate:
            fields.append(("Дата рождения", self.birthdate))
        if self.department_code:
            # Форматируем код подразделения
            dept_display = self.department_code
            if len(self.department_code) == 6:
                dept_display = f"{self.department_code[:3]}-{self.department_code[3:]}"
            fields.append(("Код подразделения", dept_display))
        if self.phone:
            fields.append(("Телефон", self.phone))
        return fields


@dataclass
class UserState:
    """
    Состояние пользователя в процессе взаимодействия с ботом.
    
    Attributes:
        state: Текущее состояние FSM (BlacklistAddState или CheckState)
        data: Собранные данные для добавления в ЧС
        check_data: Данные для проверки в ЧС
        bot_message_ids: Список ID сообщений бота (для удаления)
    """
    state: StateType = None
    data: BlacklistCollectionData = field(default_factory=BlacklistCollectionData)
    check_data: CheckSearchData = field(default_factory=CheckSearchData)
    bot_message_ids: list = field(default_factory=list)


class UserStateStorage:
    """
    Потокобезопасное хранилище состояний пользователей.
    Каждый пользователь имеет свой независимый буфер.
    """
    
    def __init__(self):
        self._states: Dict[int, UserState] = {}
        self._lock = asyncio.Lock()
    
    async def get_state(self, user_id: int) -> StateType:
        """
        Получить текущее состояние пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Текущее состояние или None
        """
        async with self._lock:
            user_state = self._states.get(user_id)
            return user_state.state if user_state else None
    
    async def set_state(self, user_id: int, state: StateType) -> None:
        """
        Установить состояние пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            state: Новое состояние (BlacklistAddState, CheckState или None)
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            self._states[user_id].state = state
            logger.debug(f"Состояние пользователя {user_id} изменено на {state}")
    
    async def get_data(self, user_id: int) -> BlacklistCollectionData:
        """
        Получить собранные данные пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Данные сбора (новый объект, если пользователь не найден)
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            return self._states[user_id].data
    
    async def update_data(self, user_id: int, **kwargs) -> None:
        """
        Обновить данные пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            **kwargs: Поля для обновления (fio, birthdate, passport и т.д.)
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            
            data = self._states[user_id].data
            for key, value in kwargs.items():
                if hasattr(data, key):
                    setattr(data, key, value)
            
            logger.debug(f"Данные пользователя {user_id} обновлены: {kwargs}")
    
    async def add_bot_message(self, user_id: int, message_id: int) -> None:
        """
        Добавить ID сообщения бота в список для последующего удаления.
        
        Args:
            user_id: Telegram ID пользователя
            message_id: ID сообщения
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            self._states[user_id].bot_message_ids.append(message_id)
    
    async def set_bot_messages(self, user_id: int, message_ids: list) -> None:
        """
        Установить список ID сообщений бота (заменяет предыдущий список).
        
        Args:
            user_id: Telegram ID пользователя
            message_ids: Список ID сообщений
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            self._states[user_id].bot_message_ids = list(message_ids)
    
    async def get_bot_messages(self, user_id: int) -> list:
        """
        Получить список ID сообщений бота.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Список ID сообщений (пустой список если нет)
        """
        async with self._lock:
            user_state = self._states.get(user_id)
            return list(user_state.bot_message_ids) if user_state else []
    
    async def clear_bot_messages(self, user_id: int) -> list:
        """
        Очистить и вернуть список ID сообщений бота.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Список ID сообщений, которые были очищены
        """
        async with self._lock:
            if user_id not in self._states:
                return []
            messages = list(self._states[user_id].bot_message_ids)
            self._states[user_id].bot_message_ids = []
            return messages
    
    # Алиасы для обратной совместимости
    async def set_last_bot_message(self, user_id: int, message_id: int) -> None:
        """Алиас для set_bot_messages с одним сообщением."""
        await self.set_bot_messages(user_id, [message_id])
    
    async def get_last_bot_message(self, user_id: int) -> Optional[int]:
        """Получить последний ID сообщения бота (для совместимости)."""
        messages = await self.get_bot_messages(user_id)
        return messages[-1] if messages else None
    
    async def clear(self, user_id: int) -> None:
        """
        Полностью очистить состояние пользователя.
        
        Args:
            user_id: Telegram ID пользователя
        """
        async with self._lock:
            if user_id in self._states:
                del self._states[user_id]
                logger.debug(f"Состояние пользователя {user_id} очищено")
    
    async def reset_data(self, user_id: int) -> None:
        """
        Сбросить только данные добавления, сохранив состояние.
        
        Args:
            user_id: Telegram ID пользователя
        """
        async with self._lock:
            if user_id in self._states:
                self._states[user_id].data = BlacklistCollectionData()
                logger.debug(f"Данные пользователя {user_id} сброшены")
    
    async def get_check_data(self, user_id: int) -> CheckSearchData:
        """
        Получить данные для проверки пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Данные для проверки (новый объект если нет)
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            return self._states[user_id].check_data
    
    async def set_check_data(self, user_id: int, check_data: CheckSearchData) -> None:
        """
        Установить данные для проверки.
        
        Args:
            user_id: Telegram ID пользователя
            check_data: Данные для проверки
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            self._states[user_id].check_data = check_data
            logger.debug(f"Данные проверки пользователя {user_id} установлены")
    
    async def reset_check_data(self, user_id: int) -> None:
        """
        Сбросить только данные проверки, сохранив состояние.
        
        Args:
            user_id: Telegram ID пользователя
        """
        async with self._lock:
            if user_id in self._states:
                self._states[user_id].check_data = CheckSearchData()
                logger.debug(f"Данные проверки пользователя {user_id} сброшены")
    
    async def is_collecting(self, user_id: int) -> bool:
        """
        Проверить, находится ли пользователь в процессе взаимодействия.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если пользователь в процессе (добавление или проверка)
        """
        state = await self.get_state(user_id)
        return state is not None
    
    async def is_checking(self, user_id: int) -> bool:
        """
        Проверить, находится ли пользователь в процессе проверки ЧС.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если пользователь в процессе проверки
        """
        state = await self.get_state(user_id)
        return isinstance(state, CheckState)
    
    async def is_adding(self, user_id: int) -> bool:
        """
        Проверить, находится ли пользователь в процессе добавления в ЧС.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если пользователь в процессе добавления
        """
        state = await self.get_state(user_id)
        return isinstance(state, BlacklistAddState)


# Глобальный экземпляр хранилища
user_state_storage = UserStateStorage()
