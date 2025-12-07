"""
Доменная сущность организации.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Organization:
    """
    Организация в системе.
    
    Attributes:
        id: Уникальный идентификатор
        name: Название организации
        hash_salt: Соль для хеширования персональных данных
        created: Дата и время создания
        updated: Дата и время последнего обновления
    """
    id: int
    name: str
    hash_salt: str
    created: datetime
    updated: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> "Organization":
        """
        Создать объект из строки БД.
        
        Args:
            row: Словарь с данными из БД
            
        Returns:
            Экземпляр Organization
        """
        return cls(
            id=row["id"],
            name=row["name"],
            hash_salt=row["hash_salt"],
            created=row["created"],
            updated=row["updated"],
        )

