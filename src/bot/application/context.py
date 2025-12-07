"""
Контекст приложения для хранения зависимостей.
Используется для передачи сервисов в обработчики.
"""
from typing import Optional

from src.db.connection import DatabaseManager
from src.bot.repo.admin_repository import AdminRepository
from src.bot.service.access_service import AccessService


class BotContext:
    """Контекст приложения с зависимостями."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация контекста.
        
        Args:
            db_manager: Менеджер подключения к базе данных
        """
        self.db_manager = db_manager
        self._admin_repository: Optional[AdminRepository] = None
        self._access_service: Optional[AccessService] = None
    
    @property
    def admin_repository(self) -> AdminRepository:
        """Получить репозиторий администраторов (lazy initialization)."""
        if self._admin_repository is None:
            self._admin_repository = AdminRepository(self.db_manager)
        return self._admin_repository
    
    @property
    def access_service(self) -> AccessService:
        """Получить сервис доступа (lazy initialization)."""
        if self._access_service is None:
            self._access_service = AccessService(self.admin_repository)
        return self._access_service

