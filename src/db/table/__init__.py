"""
Модуль таблиц базы данных.
Содержит SQL схемы и функции инициализации таблиц.
"""
import logging

from src.db.connection import DatabaseManager
from src.db.table.base import UPDATE_TIMESTAMP_FUNCTION_SQL
from src.db.table import admins
from src.db.table import organizations
from src.db.table import admin_organizations
from src.db.table import blacklist_persons
from src.db.table import blacklist_records
from src.db.table import blacklist_history

logger = logging.getLogger(__name__)


async def initialize_tables(db_manager: DatabaseManager) -> None:
    """
    Инициализировать все таблицы базы данных.
    
    Порядок создания важен из-за внешних ключей:
    1. admins — базовая таблица
    2. organizations — базовая таблица
    3. admin_organizations — зависит от admins и organizations
    4. blacklist_persons — зависит от organizations (обезличенные пользователи)
    5. blacklist_records — зависит от blacklist_persons и admins
    6. blacklist_history — зависит от blacklist_records и admins
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Инициализация таблиц базы данных...")
        
        # Создаем функцию для обновления timestamp (нужна для всех таблиц)
        await db_manager.execute(UPDATE_TIMESTAMP_FUNCTION_SQL)
        logger.debug("Функция update_updated_column создана")
        
        # Базовые таблицы
        await admins.create_table(db_manager)
        await organizations.create_table(db_manager)
        
        # Таблицы с зависимостями от базовых
        await admin_organizations.create_table(db_manager)
        
        # Таблицы черного списка
        await blacklist_persons.create_table(db_manager)
        await blacklist_records.create_table(db_manager)
        await blacklist_history.create_table(db_manager)
        
        logger.info("Все таблицы успешно инициализированы")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации таблиц: {e}", exc_info=True)
        raise


__all__ = ["initialize_tables"]

