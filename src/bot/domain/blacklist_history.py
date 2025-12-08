"""
Доменная сущность истории изменений черного списка.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class BlacklistAction(str, Enum):
    """Типы действий с записью черного списка."""
    ADDED = "added"
    UPDATED = "updated"
    DEACTIVATED = "deactivated"
    REACTIVATED = "reactivated"


@dataclass
class BlacklistHistory:
    """
    Запись истории изменений черного списка.
    
    Attributes:
        id: Уникальный числовой идентификатор (SERIAL)
        blacklist_record_id: UUID записи черного списка
        action: Тип действия
        changed_by_admin_id: UUID админа, выполнившего действие
        old_reason: Предыдущая причина (для обновлений)
        new_reason: Новая причина (для обновлений)
        old_status: Предыдущий статус
        new_status: Новый статус
        comment: Комментарий к изменению
        created: Дата и время изменения
    """
    id: int
    blacklist_record_id: UUID
    action: BlacklistAction
    changed_by_admin_id: Optional[UUID]
    old_reason: Optional[str]
    new_reason: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    comment: Optional[str]
    created: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> "BlacklistHistory":
        """
        Создать объект из строки БД.
        
        Args:
            row: Словарь с данными из БД
            
        Returns:
            Экземпляр BlacklistHistory
        """
        admin_id = row.get("changed_by_admin_id")
        
        return cls(
            id=int(row["id"]),
            blacklist_record_id=UUID(str(row["blacklist_record_id"])),
            action=BlacklistAction(row["action"]),
            changed_by_admin_id=UUID(str(admin_id)) if admin_id else None,
            old_reason=row.get("old_reason"),
            new_reason=row.get("new_reason"),
            old_status=row.get("old_status"),
            new_status=row.get("new_status"),
            comment=row.get("comment"),
            created=row["created"],
        )

