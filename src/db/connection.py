"""
Менеджер подключения к базе данных.
Обеспечивает инициализацию и управление соединением с БД.
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection

from src.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных."""
    
    def __init__(self, config: DatabaseConfig):
        """
        Инициализация менеджера БД.
        
        Args:
            config: Конфигурация базы данных
        """
        self.config = config
        self.pool: Optional[Pool] = None
    
    async def initialize(self) -> None:
        """Инициализация пула подключений к БД."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=2,
                max_size=10,
            )
            logger.info("Пул подключений к БД создан")
            
            # Проверка подключения
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("Подключение к БД успешно проверено")
            
        except Exception as e:
            logger.error(f"Ошибка при создании пула подключений: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Получить соединение с БД из пула (context manager).
        
        Yields:
            Connection: Соединение с базой данных
        """
        if not self.pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """
        Выполнить SQL запрос.
        
        Args:
            query: SQL запрос
            *args: Параметры запроса
            
        Returns:
            Результат выполнения запроса
        """
        if not self.pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """
        Выполнить SELECT запрос и получить результаты.
        
        Args:
            query: SQL запрос
            *args: Параметры запроса
            
        Returns:
            Список результатов
        """
        if not self.pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """
        Выполнить SELECT запрос и получить одну строку.
        
        Args:
            query: SQL запрос
            *args: Параметры запроса
            
        Returns:
            Результат запроса или None
        """
        if not self.pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def close(self) -> None:
        """Закрыть пул подключений."""
        if self.pool:
            await self.pool.close()
            logger.info("Пул подключений к БД закрыт")

