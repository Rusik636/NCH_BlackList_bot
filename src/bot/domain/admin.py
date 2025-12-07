"""
Доменная сущность администратора.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.bot.domain.role import Role


@dataclass
class Admin:
    """
    Доменная сущность администратора.
    
    Attributes:
        id: Уникальный идентификатор (UUID)
        admin_id: Telegram ID администратора
        role: Роль администратора
        created: Дата и время создания записи
        updated: Дата и время последнего обновления записи
    """
    id: UUID
    admin_id: int
    role: Role
    created: datetime
    updated: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> "Admin":
        """
        Создать объект Admin из строки базы данных.
        
        Args:
            row: Словарь с данными из БД
            
        Returns:
            Объект Admin
        """
        # Обработка UUID: asyncpg возвращает свой тип UUID, преобразуем в стандартный Python UUID
        row_id = row["id"]
        # Преобразуем в строку, затем в стандартный UUID
        # Это работает как для asyncpg UUID, так и для строк
        admin_uuid = UUID(str(row_id))
        
        return cls(
            id=admin_uuid,
            admin_id=int(row["admin_id"]),
            role=Role.from_string(row["role"]),
            created=row["created"],
            updated=row["updated"],
        )

