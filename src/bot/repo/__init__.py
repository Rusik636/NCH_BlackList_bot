"""Слой репозиториев (data access layer)."""

from src.bot.repo.admin_repository import AdminRepository
from src.bot.repo.organization_repository import OrganizationRepository
from src.bot.repo.blacklist_person_repository import BlacklistPersonRepository
from src.bot.repo.blacklist_record_repository import BlacklistRecordRepository
from src.bot.repo.blacklist_history_repository import BlacklistHistoryRepository

__all__ = [
    "AdminRepository",
    "OrganizationRepository",
    "BlacklistPersonRepository",
    "BlacklistRecordRepository",
    "BlacklistHistoryRepository",
]
