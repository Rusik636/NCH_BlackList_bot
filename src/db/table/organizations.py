"""
Таблица организаций.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Создание таблицы организаций
# hash_salt — уникальная соль для хеширования персональных данных (генерируется при создании)
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    hash_salt VARCHAR(64) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для быстрого поиска по названию организации
NAME_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);
"""

# Удаление триггера для организаций
DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_organizations_updated ON organizations;
"""

# Создание триггера для автоматического обновления поля updated
CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_organizations_updated
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу организаций в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы organizations...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица organizations создана")
        
        # Создаем индекс для поиска по названию
        await db_manager.execute(NAME_INDEX_SQL)
        logger.debug("Индекс idx_organizations_name создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_organizations_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_organizations_updated создан")
        
        logger.info("Таблица organizations успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы organizations: {e}", exc_info=True)
        raise

