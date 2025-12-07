"""
Репозиторий для работы с администраторами в базе данных.
"""
import logging
from typing import Optional

from src.db.connection import DatabaseManager
from src.bot.domain.admin import Admin
from src.bot.domain.role import Role

logger = logging.getLogger(__name__)


class AdminRepository:
    """Репозиторий для работы с администраторами."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация репозитория.
        
        Args:
            db_manager: Менеджер подключения к базе данных
        """
        self.db_manager = db_manager
    
    async def get_by_admin_id(self, admin_id: int) -> Optional[Admin]:
        """
        Получить администратора по Telegram ID.
        
        Args:
            admin_id: Telegram ID администратора
            
        Returns:
            Объект Admin или None, если не найден
        """
        try:
            query = """
                SELECT id, admin_id, role, created, updated
                FROM admins
                WHERE admin_id = $1
            """
            row = await self.db_manager.fetchrow(query, admin_id)
            
            if row:
                return Admin.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении администратора по admin_id {admin_id}: {e}", exc_info=True)
            raise
    
    async def exists(self, admin_id: int) -> bool:
        """
        Проверить, существует ли администратор с указанным Telegram ID.
        
        Args:
            admin_id: Telegram ID администратора
            
        Returns:
            True, если администратор существует, False иначе
        """
        try:
            query = "SELECT EXISTS(SELECT 1 FROM admins WHERE admin_id = $1)"
            result = await self.db_manager.fetchrow(query, admin_id)
            return result["exists"] if result else False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке существования администратора {admin_id}: {e}", exc_info=True)
            raise
    
    async def create(self, admin_id: int, role: Role) -> Admin:
        """
        Создать нового администратора.
        
        Args:
            admin_id: Telegram ID администратора
            role: Роль администратора
            
        Returns:
            Созданный объект Admin
            
        Raises:
            ValueError: Если администратор с таким ID уже существует
        """
        try:
            # Проверяем, не существует ли уже администратор
            if await self.exists(admin_id):
                raise ValueError(f"Администратор с ID {admin_id} уже существует")
            
            query = """
                INSERT INTO admins (admin_id, role)
                VALUES ($1, $2)
                RETURNING id, admin_id, role, created, updated
            """
            row = await self.db_manager.fetchrow(query, admin_id, role.value)
            
            if row:
                return Admin.from_db_row(row)
            raise RuntimeError("Не удалось создать администратора")
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании администратора {admin_id}: {e}", exc_info=True)
            raise

