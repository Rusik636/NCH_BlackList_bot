"""
Хранилище состояний пользователей.
Потокобезопасное хранение данных сбора для каждого пользователя.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from src.bot.application.states import BlacklistAddState

logger = logging.getLogger(__name__)


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
        started_at: Время начала сбора данных
    """
    fio: Optional[str] = None
    birthdate: Optional[str] = None
    passport: Optional[str] = None
    department_code: Optional[str] = None
    phone: Optional[str] = None
    reason: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserState:
    """
    Состояние пользователя в процессе взаимодействия с ботом.
    
    Attributes:
        state: Текущее состояние FSM
        data: Собранные данные
        last_bot_message_id: ID последнего сообщения бота (для удаления)
    """
    state: Optional[BlacklistAddState] = None
    data: BlacklistCollectionData = field(default_factory=BlacklistCollectionData)
    last_bot_message_id: Optional[int] = None


class UserStateStorage:
    """
    Потокобезопасное хранилище состояний пользователей.
    Каждый пользователь имеет свой независимый буфер.
    """
    
    def __init__(self):
        self._states: Dict[int, UserState] = {}
        self._lock = asyncio.Lock()
    
    async def get_state(self, user_id: int) -> Optional[BlacklistAddState]:
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
    
    async def set_state(self, user_id: int, state: Optional[BlacklistAddState]) -> None:
        """
        Установить состояние пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            state: Новое состояние (None для сброса)
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
    
    async def set_last_bot_message(self, user_id: int, message_id: int) -> None:
        """
        Сохранить ID последнего сообщения бота.
        
        Args:
            user_id: Telegram ID пользователя
            message_id: ID сообщения
        """
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
            self._states[user_id].last_bot_message_id = message_id
    
    async def get_last_bot_message(self, user_id: int) -> Optional[int]:
        """
        Получить ID последнего сообщения бота.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            ID сообщения или None
        """
        async with self._lock:
            user_state = self._states.get(user_id)
            return user_state.last_bot_message_id if user_state else None
    
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
        Сбросить только данные, сохранив состояние.
        
        Args:
            user_id: Telegram ID пользователя
        """
        async with self._lock:
            if user_id in self._states:
                self._states[user_id].data = BlacklistCollectionData()
                logger.debug(f"Данные пользователя {user_id} сброшены")
    
    async def is_collecting(self, user_id: int) -> bool:
        """
        Проверить, находится ли пользователь в процессе сбора данных.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если пользователь в процессе сбора
        """
        state = await self.get_state(user_id)
        return state is not None


# Глобальный экземпляр хранилища
user_state_storage = UserStateStorage()

