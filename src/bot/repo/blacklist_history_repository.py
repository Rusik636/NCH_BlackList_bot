"""
Репозиторий для работы с историей изменений черного списка.
Принцип единственной ответственности (SRP): только операции с blacklist_history.
"""
import logging
from typing import Optional, List
from uuid import UUID

from src.db.connection import DatabaseManager
from src.bot.domain.blacklist_history import BlacklistHistory, BlacklistAction

logger = logging.getLogger(__name__)


class BlacklistHistoryRepository:
    """
    Репозиторий для работы с таблицей blacklist_history.
    
    Responsibilities:
        - Добавление записей истории
        - Получение истории изменений
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация репозитория.
        
        Args:
            db_manager: Менеджер подключения к БД
        """
        self._db = db_manager
    
    async def add(
        self,
        blacklist_record_id: UUID,
        action: BlacklistAction,
        changed_by_admin_id: Optional[UUID] = None,
        old_reason: Optional[str] = None,
        new_reason: Optional[str] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> BlacklistHistory:
        """
        Добавить запись в историю.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            action: Тип действия
            changed_by_admin_id: UUID админа (опционально)
            old_reason: Предыдущая причина
            new_reason: Новая причина
            old_status: Предыдущий статус
            new_status: Новый статус
            comment: Комментарий
            
        Returns:
            Созданная запись истории
        """
        try:
            query = """
                INSERT INTO blacklist_history (
                    blacklist_record_id,
                    action,
                    changed_by_admin_id,
                    old_reason,
                    new_reason,
                    old_status,
                    new_status,
                    comment
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """
            
            row = await self._db.fetchrow(
                query,
                blacklist_record_id,
                action.value,
                changed_by_admin_id,
                old_reason,
                new_reason,
                old_status,
                new_status,
                comment,
            )
            
            if not row:
                raise ValueError("Не удалось создать запись истории")
            
            history = BlacklistHistory.from_db_row(row)
            logger.debug(f"Добавлена запись истории: {action.value} для {blacklist_record_id}")
            
            return history
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении записи истории: {e}", exc_info=True)
            raise
    
    async def log_added(
        self,
        blacklist_record_id: UUID,
        admin_id: UUID,
        reason: str,
        comment: Optional[str] = None,
    ) -> BlacklistHistory:
        """
        Записать добавление в ЧС.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            admin_id: UUID админа
            reason: Причина добавления
            comment: Комментарий
            
        Returns:
            Запись истории
        """
        return await self.add(
            blacklist_record_id=blacklist_record_id,
            action=BlacklistAction.ADDED,
            changed_by_admin_id=admin_id,
            new_reason=reason,
            new_status="active",
            comment=comment,
        )
    
    async def log_updated(
        self,
        blacklist_record_id: UUID,
        admin_id: UUID,
        old_reason: str,
        new_reason: str,
        comment: Optional[str] = None,
    ) -> BlacklistHistory:
        """
        Записать обновление причины.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            admin_id: UUID админа
            old_reason: Предыдущая причина
            new_reason: Новая причина
            comment: Комментарий
            
        Returns:
            Запись истории
        """
        return await self.add(
            blacklist_record_id=blacklist_record_id,
            action=BlacklistAction.UPDATED,
            changed_by_admin_id=admin_id,
            old_reason=old_reason,
            new_reason=new_reason,
            comment=comment,
        )
    
    async def log_deactivated(
        self,
        blacklist_record_id: UUID,
        admin_id: UUID,
        comment: Optional[str] = None,
    ) -> BlacklistHistory:
        """
        Записать деактивацию.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            admin_id: UUID админа
            comment: Комментарий/причина деактивации
            
        Returns:
            Запись истории
        """
        return await self.add(
            blacklist_record_id=blacklist_record_id,
            action=BlacklistAction.DEACTIVATED,
            changed_by_admin_id=admin_id,
            old_status="active",
            new_status="inactive",
            comment=comment,
        )
    
    async def log_reactivated(
        self,
        blacklist_record_id: UUID,
        admin_id: UUID,
        comment: Optional[str] = None,
    ) -> BlacklistHistory:
        """
        Записать реактивацию.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            admin_id: UUID админа
            comment: Комментарий/причина реактивации
            
        Returns:
            Запись истории
        """
        return await self.add(
            blacklist_record_id=blacklist_record_id,
            action=BlacklistAction.REACTIVATED,
            changed_by_admin_id=admin_id,
            old_status="inactive",
            new_status="active",
            comment=comment,
        )
    
    async def get_by_record_id(
        self,
        blacklist_record_id: UUID,
        limit: int = 50,
    ) -> List[BlacklistHistory]:
        """
        Получить историю изменений записи.
        
        Args:
            blacklist_record_id: UUID записи ЧС
            limit: Максимальное количество записей
            
        Returns:
            Список записей истории (от новых к старым)
        """
        try:
            query = """
                SELECT * FROM blacklist_history
                WHERE blacklist_record_id = $1
                ORDER BY created DESC
                LIMIT $2
            """
            
            rows = await self._db.fetch(query, blacklist_record_id, limit)
            return [BlacklistHistory.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории для {blacklist_record_id}: {e}", exc_info=True)
            raise
    
    async def get_by_admin(
        self,
        admin_id: UUID,
        limit: int = 50,
    ) -> List[BlacklistHistory]:
        """
        Получить историю действий админа.
        
        Args:
            admin_id: UUID админа
            limit: Максимальное количество записей
            
        Returns:
            Список записей истории
        """
        try:
            query = """
                SELECT * FROM blacklist_history
                WHERE changed_by_admin_id = $1
                ORDER BY created DESC
                LIMIT $2
            """
            
            rows = await self._db.fetch(query, admin_id, limit)
            return [BlacklistHistory.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории админа {admin_id}: {e}", exc_info=True)
            raise
    
    async def get_recent(
        self,
        limit: int = 50,
        action: Optional[BlacklistAction] = None,
    ) -> List[BlacklistHistory]:
        """
        Получить последние записи истории.
        
        Args:
            limit: Максимальное количество записей
            action: Фильтр по типу действия (опционально)
            
        Returns:
            Список записей истории
        """
        try:
            if action:
                query = """
                    SELECT * FROM blacklist_history
                    WHERE action = $1
                    ORDER BY created DESC
                    LIMIT $2
                """
                rows = await self._db.fetch(query, action.value, limit)
            else:
                query = """
                    SELECT * FROM blacklist_history
                    ORDER BY created DESC
                    LIMIT $1
                """
                rows = await self._db.fetch(query, limit)
            
            return [BlacklistHistory.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении последних записей истории: {e}", exc_info=True)
            raise

