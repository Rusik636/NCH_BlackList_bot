"""
Репозиторий для работы с записями черного списка.
Принцип единственной ответственности (SRP): только CRUD операции с blacklist_records.
"""
import logging
from typing import Optional, List
from uuid import UUID

from src.db.connection import DatabaseManager
from src.bot.domain.blacklist_record import BlacklistRecord, BlacklistStatus

logger = logging.getLogger(__name__)


class BlacklistRecordRepository:
    """
    Репозиторий для работы с таблицей blacklist_records.
    
    Responsibilities:
        - CRUD операции с записями черного списка
        - Фильтрация по статусу, организации, пользователю
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация репозитория.
        
        Args:
            db_manager: Менеджер подключения к БД
        """
        self._db = db_manager
    
    async def create(
        self,
        person_id: UUID,
        organization_id: int,
        added_by_admin_id: UUID,
        reason: str,
        comment: Optional[str] = None,
    ) -> BlacklistRecord:
        """
        Создать запись в черном списке.
        
        Args:
            person_id: UUID обезличенного пользователя
            organization_id: ID организации
            added_by_admin_id: UUID админа
            reason: Причина добавления
            comment: Комментарий (опционально)
            
        Returns:
            Созданная запись BlacklistRecord
            
        Raises:
            Exception: При ошибке создания
        """
        try:
            query = """
                INSERT INTO blacklist_records (
                    person_id,
                    organization_id,
                    added_by_admin_id,
                    reason,
                    comment,
                    status
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            
            row = await self._db.fetchrow(
                query,
                person_id,
                organization_id,
                added_by_admin_id,
                reason,
                comment,
                BlacklistStatus.ACTIVE.value,
            )
            
            if not row:
                raise ValueError("Не удалось создать запись в черном списке")
            
            record = BlacklistRecord.from_db_row(row)
            logger.info(f"Создана запись в ЧС: {record.id} для пользователя {person_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Ошибка при создании записи в ЧС: {e}", exc_info=True)
            raise
    
    async def get_by_id(self, record_id: UUID) -> Optional[BlacklistRecord]:
        """
        Получить запись по ID.
        
        Args:
            record_id: UUID записи
            
        Returns:
            BlacklistRecord или None
        """
        try:
            query = "SELECT * FROM blacklist_records WHERE id = $1"
            row = await self._db.fetchrow(query, record_id)
            
            if row:
                return BlacklistRecord.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении записи {record_id}: {e}", exc_info=True)
            raise
    
    async def get_by_person_id(
        self,
        person_id: UUID,
        status: Optional[BlacklistStatus] = None,
    ) -> List[BlacklistRecord]:
        """
        Получить все записи для обезличенного пользователя.
        
        Args:
            person_id: UUID пользователя
            status: Фильтр по статусу (опционально)
            
        Returns:
            Список записей
        """
        try:
            if status:
                query = """
                    SELECT * FROM blacklist_records
                    WHERE person_id = $1 AND status = $2
                    ORDER BY created DESC
                """
                rows = await self._db.fetch(query, person_id, status.value)
            else:
                query = """
                    SELECT * FROM blacklist_records
                    WHERE person_id = $1
                    ORDER BY created DESC
                """
                rows = await self._db.fetch(query, person_id)
            
            return [BlacklistRecord.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении записей для {person_id}: {e}", exc_info=True)
            raise
    
    async def get_by_organization(
        self,
        organization_id: int,
        status: Optional[BlacklistStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BlacklistRecord]:
        """
        Получить записи организации.
        
        Args:
            organization_id: ID организации
            status: Фильтр по статусу (опционально)
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список записей
        """
        try:
            if status:
                query = """
                    SELECT * FROM blacklist_records
                    WHERE organization_id = $1 AND status = $2
                    ORDER BY created DESC
                    LIMIT $3 OFFSET $4
                """
                rows = await self._db.fetch(query, organization_id, status.value, limit, offset)
            else:
                query = """
                    SELECT * FROM blacklist_records
                    WHERE organization_id = $1
                    ORDER BY created DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await self._db.fetch(query, organization_id, limit, offset)
            
            return [BlacklistRecord.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении записей организации {organization_id}: {e}", exc_info=True)
            raise
    
    async def get_active_by_person(self, person_id: UUID) -> Optional[BlacklistRecord]:
        """
        Получить активную запись для пользователя.
        
        Args:
            person_id: UUID пользователя
            
        Returns:
            Активная запись или None
        """
        try:
            query = """
                SELECT * FROM blacklist_records
                WHERE person_id = $1 AND status = $2
                ORDER BY created DESC
                LIMIT 1
            """
            
            row = await self._db.fetchrow(query, person_id, BlacklistStatus.ACTIVE.value)
            
            if row:
                return BlacklistRecord.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении активной записи для {person_id}: {e}", exc_info=True)
            raise
    
    async def update_status(
        self,
        record_id: UUID,
        new_status: BlacklistStatus,
    ) -> Optional[BlacklistRecord]:
        """
        Обновить статус записи.
        
        Args:
            record_id: UUID записи
            new_status: Новый статус
            
        Returns:
            Обновленная запись или None
        """
        try:
            query = """
                UPDATE blacklist_records
                SET status = $2
                WHERE id = $1
                RETURNING *
            """
            
            row = await self._db.fetchrow(query, record_id, new_status.value)
            
            if row:
                record = BlacklistRecord.from_db_row(row)
                logger.info(f"Обновлен статус записи {record_id}: {new_status.value}")
                return record
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса записи {record_id}: {e}", exc_info=True)
            raise
    
    async def update_reason(
        self,
        record_id: UUID,
        new_reason: str,
        new_comment: Optional[str] = None,
    ) -> Optional[BlacklistRecord]:
        """
        Обновить причину записи.
        
        Args:
            record_id: UUID записи
            new_reason: Новая причина
            new_comment: Новый комментарий (опционально)
            
        Returns:
            Обновленная запись или None
        """
        try:
            query = """
                UPDATE blacklist_records
                SET reason = $2, comment = $3
                WHERE id = $1
                RETURNING *
            """
            
            row = await self._db.fetchrow(query, record_id, new_reason, new_comment)
            
            if row:
                record = BlacklistRecord.from_db_row(row)
                logger.info(f"Обновлена причина записи {record_id}")
                return record
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении причины записи {record_id}: {e}", exc_info=True)
            raise
    
    async def deactivate(self, record_id: UUID) -> Optional[BlacklistRecord]:
        """
        Деактивировать запись (мягкое удаление).
        
        Args:
            record_id: UUID записи
            
        Returns:
            Деактивированная запись или None
        """
        return await self.update_status(record_id, BlacklistStatus.INACTIVE)
    
    async def reactivate(self, record_id: UUID) -> Optional[BlacklistRecord]:
        """
        Реактивировать запись.
        
        Args:
            record_id: UUID записи
            
        Returns:
            Реактивированная запись или None
        """
        return await self.update_status(record_id, BlacklistStatus.ACTIVE)
    
    async def count_by_organization(
        self,
        organization_id: int,
        status: Optional[BlacklistStatus] = None,
    ) -> int:
        """
        Подсчитать записи организации.
        
        Args:
            organization_id: ID организации
            status: Фильтр по статусу (опционально)
            
        Returns:
            Количество записей
        """
        try:
            if status:
                query = """
                    SELECT COUNT(*) as count FROM blacklist_records
                    WHERE organization_id = $1 AND status = $2
                """
                row = await self._db.fetchrow(query, organization_id, status.value)
            else:
                query = """
                    SELECT COUNT(*) as count FROM blacklist_records
                    WHERE organization_id = $1
                """
                row = await self._db.fetchrow(query, organization_id)
            
            return row["count"] if row else 0
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете записей организации {organization_id}: {e}", exc_info=True)
            raise
    
    async def delete(self, record_id: UUID) -> bool:
        """
        Удалить запись (жесткое удаление).
        Рекомендуется использовать deactivate() вместо delete().
        
        Args:
            record_id: UUID записи
            
        Returns:
            True если удалена
        """
        try:
            query = "DELETE FROM blacklist_records WHERE id = $1 RETURNING id"
            row = await self._db.fetchrow(query, record_id)
            
            if row:
                logger.warning(f"Жестко удалена запись ЧС: {record_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при удалении записи {record_id}: {e}", exc_info=True)
            raise

