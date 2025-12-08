"""
Контекст приложения для хранения зависимостей.
Используется для передачи сервисов в обработчики.
"""
from typing import Optional

from src.db.connection import DatabaseManager
from src.config import get_config

# Репозитории
from src.bot.repo.admin_repository import AdminRepository
from src.bot.repo.organization_repository import OrganizationRepository
from src.bot.repo.blacklist_person_repository import BlacklistPersonRepository
from src.bot.repo.blacklist_record_repository import BlacklistRecordRepository
from src.bot.repo.blacklist_history_repository import BlacklistHistoryRepository

# Сервисы
from src.bot.service.access_service import AccessService
from src.bot.service.hash_service import HashService
from src.bot.service.blacklist_service import BlacklistService


class BotContext:
    """Контекст приложения с зависимостями."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация контекста.
        
        Args:
            db_manager: Менеджер подключения к базе данных
        """
        self.db_manager = db_manager
        self._config = get_config()
        
        # Репозитории (lazy initialization)
        self._admin_repository: Optional[AdminRepository] = None
        self._organization_repository: Optional[OrganizationRepository] = None
        self._blacklist_person_repository: Optional[BlacklistPersonRepository] = None
        self._blacklist_record_repository: Optional[BlacklistRecordRepository] = None
        self._blacklist_history_repository: Optional[BlacklistHistoryRepository] = None
        
        # Сервисы (lazy initialization)
        self._access_service: Optional[AccessService] = None
        self._hash_service: Optional[HashService] = None
        self._blacklist_service: Optional[BlacklistService] = None
    
    # =========================================================================
    # Репозитории
    # =========================================================================
    
    @property
    def admin_repository(self) -> AdminRepository:
        """Получить репозиторий администраторов."""
        if self._admin_repository is None:
            self._admin_repository = AdminRepository(self.db_manager)
        return self._admin_repository
    
    @property
    def organization_repository(self) -> OrganizationRepository:
        """Получить репозиторий организаций."""
        if self._organization_repository is None:
            self._organization_repository = OrganizationRepository(self.db_manager)
        return self._organization_repository
    
    @property
    def blacklist_person_repository(self) -> BlacklistPersonRepository:
        """Получить репозиторий обезличенных пользователей."""
        if self._blacklist_person_repository is None:
            self._blacklist_person_repository = BlacklistPersonRepository(self.db_manager)
        return self._blacklist_person_repository
    
    @property
    def blacklist_record_repository(self) -> BlacklistRecordRepository:
        """Получить репозиторий записей черного списка."""
        if self._blacklist_record_repository is None:
            self._blacklist_record_repository = BlacklistRecordRepository(self.db_manager)
        return self._blacklist_record_repository
    
    @property
    def blacklist_history_repository(self) -> BlacklistHistoryRepository:
        """Получить репозиторий истории черного списка."""
        if self._blacklist_history_repository is None:
            self._blacklist_history_repository = BlacklistHistoryRepository(self.db_manager)
        return self._blacklist_history_repository
    
    # =========================================================================
    # Сервисы
    # =========================================================================
    
    @property
    def access_service(self) -> AccessService:
        """Получить сервис доступа."""
        if self._access_service is None:
            self._access_service = AccessService(self.admin_repository)
        return self._access_service
    
    @property
    def hash_service(self) -> HashService:
        """Получить сервис хеширования."""
        if self._hash_service is None:
            self._hash_service = HashService(self._config.security.hash_pepper)
        return self._hash_service
    
    @property
    def blacklist_service(self) -> BlacklistService:
        """Получить сервис черного списка."""
        if self._blacklist_service is None:
            self._blacklist_service = BlacklistService(
                organization_repo=self.organization_repository,
                person_repo=self.blacklist_person_repository,
                record_repo=self.blacklist_record_repository,
                history_repo=self.blacklist_history_repository,
                hash_service=self.hash_service,
            )
        return self._blacklist_service


# Глобальный экземпляр контекста (устанавливается при инициализации бота)
_bot_context: Optional[BotContext] = None


def set_bot_context(context: BotContext) -> None:
    """Установить глобальный контекст приложения."""
    global _bot_context
    _bot_context = context


def get_bot_context() -> BotContext:
    """Получить глобальный контекст приложения."""
    if _bot_context is None:
        raise RuntimeError("Контекст приложения не инициализирован")
    return _bot_context

