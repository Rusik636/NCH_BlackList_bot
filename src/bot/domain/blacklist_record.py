"""
Доменная сущность записи черного списка.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class BlacklistStatus(str, Enum):
    """Статусы записи в черном списке."""
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class BlacklistRecord:
    """
    Запись в черном списке.
    Связывает обезличенного пользователя с причиной и организацией.
    
    Attributes:
        id: Уникальный UUID идентификатор
        person_id: ID обезличенного пользователя
        organization_id: ID организации, добавившей запись
        added_by_admin_id: UUID админа, добавившего запись
        reason: Причина добавления в ЧС
        comment: Дополнительный комментарий
        status: Статус записи (active/inactive)
        created: Дата и время создания
        updated: Дата и время последнего обновления
    """
    id: UUID
    person_id: UUID
    organization_id: int
    added_by_admin_id: UUID
    reason: str
    comment: Optional[str]
    status: BlacklistStatus
    created: datetime
    updated: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> "BlacklistRecord":
        """
        Создать объект из строки БД.
        
        Args:
            row: Словарь с данными из БД
            
        Returns:
            Экземпляр BlacklistRecord
        """
        return cls(
            id=UUID(str(row["id"])),
            person_id=UUID(str(row["person_id"])),
            organization_id=row["organization_id"],
            added_by_admin_id=UUID(str(row["added_by_admin_id"])),
            reason=row["reason"],
            comment=row.get("comment"),
            status=BlacklistStatus(row["status"]),
            created=row["created"],
            updated=row["updated"],
        )

