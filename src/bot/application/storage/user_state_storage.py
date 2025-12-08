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
class UserState:
    """
    Состояние пользователя в процессе взаимодействия с ботом.
    
    Attributes:
        state: Текущее состояние FSM
        data: Собранные данные
        bot_message_ids: Список ID сообщений бота (для удаления)
    """
    state: Optional[BlacklistAddState] = None
    data: BlacklistCollectionData = field(default_factory=BlacklistCollectionData)
    bot_message_ids: list = field(default_factory=list)


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

