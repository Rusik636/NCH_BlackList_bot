"""
Репозиторий для работы с организациями.
Принцип единственной ответственности (SRP): только CRUD операции с организациями.
"""
import logging
import secrets
from typing import Optional, List

from src.db.connection import DatabaseManager
from src.bot.domain.organization import Organization

logger = logging.getLogger(__name__)


class OrganizationRepository:
    """
    Репозиторий для работы с таблицей organizations.
    
    Responsibilities:
        - CRUD операции с организациями
        - Генерация соли при создании
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация репозитория.
        
        Args:
            db_manager: Менеджер подключения к БД
        """
        self._db = db_manager
    
    @staticmethod
    def _generate_salt() -> str:
        """
        Генерирует криптографически стойкую соль.
        
        Returns:
            Соль в hex-формате (64 символа)
        """
        return secrets.token_hex(32)
    
    async def create(self, name: str) -> Organization:
        """
        Создать новую организацию.
        Соль генерируется автоматически.
        
        Args:
            name: Название организации
            
        Returns:
            Созданная организация
            
        Raises:
            Exception: При ошибке создания
        """
        try:
            hash_salt = self._generate_salt()
            
            query = """
                INSERT INTO organizations (name, hash_salt)
                VALUES ($1, $2)
                RETURNING id, name, hash_salt, created, updated
            """
            
            row = await self._db.fetchrow(query, name, hash_salt)
            
            if not row:
                raise ValueError("Не удалось создать организацию")
            
            organization = Organization.from_db_row(row)
            logger.info(f"Создана организация: {organization.name} (id={organization.id})")
            
            return organization
            
        except Exception as e:
            logger.error(f"Ошибка при создании организации '{name}': {e}", exc_info=True)
            raise
    
    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """
        Получить организацию по ID.
        
        Args:
            org_id: ID организации
            
        Returns:
            Организация или None
        """
        try:
            query = """
                SELECT id, name, hash_salt, created, updated
                FROM organizations
                WHERE id = $1
            """
            
            row = await self._db.fetchrow(query, org_id)
            
            if row:
                return Organization.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении организации {org_id}: {e}", exc_info=True)
            raise
    
    async def get_by_name(self, name: str) -> Optional[Organization]:
        """
        Получить организацию по названию.
        
        Args:
            name: Название организации
            
        Returns:
            Организация или None
        """
        try:
            query = """
                SELECT id, name, hash_salt, created, updated
                FROM organizations
                WHERE name = $1
            """
            
            row = await self._db.fetchrow(query, name)
            
            if row:
                return Organization.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении организации '{name}': {e}", exc_info=True)
            raise
    
    async def get_all(self) -> List[Organization]:
        """
        Получить все организации.
        
        Returns:
            Список организаций
        """
        try:
            query = """
                SELECT id, name, hash_salt, created, updated
                FROM organizations
                ORDER BY name
            """
            
            rows = await self._db.fetch(query)
            return [Organization.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка организаций: {e}", exc_info=True)
            raise
    
    async def update_name(self, org_id: int, new_name: str) -> Optional[Organization]:
        """
        Обновить название организации.
        
        Args:
            org_id: ID организации
            new_name: Новое название
            
        Returns:
            Обновленная организация или None
        """
        try:
            query = """
                UPDATE organizations
                SET name = $2
                WHERE id = $1
                RETURNING id, name, hash_salt, created, updated
            """
            
            row = await self._db.fetchrow(query, org_id, new_name)
            
            if row:
                organization = Organization.from_db_row(row)
                logger.info(f"Обновлено название организации {org_id}: {new_name}")
                return organization
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении организации {org_id}: {e}", exc_info=True)
            raise
    
    async def delete(self, org_id: int) -> bool:
        """
        Удалить организацию.
        
        Args:
            org_id: ID организации
            
        Returns:
            True если удалена, False если не найдена
        """
        try:
            query = "DELETE FROM organizations WHERE id = $1 RETURNING id"
            row = await self._db.fetchrow(query, org_id)
            
            if row:
                logger.info(f"Удалена организация {org_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при удалении организации {org_id}: {e}", exc_info=True)
            raise
    
    async def exists(self, org_id: int) -> bool:
        """
        Проверить существование организации.
        
        Args:
            org_id: ID организации
            
        Returns:
            True если существует
        """
        try:
            query = "SELECT EXISTS(SELECT 1 FROM organizations WHERE id = $1)"
            result = await self._db.fetchrow(query, org_id)
            return result["exists"] if result else False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке организации {org_id}: {e}", exc_info=True)
            raise

