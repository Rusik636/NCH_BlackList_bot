"""
Таблица связей админов и организаций.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Создание таблицы связей
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admin_organizations (
    id SERIAL PRIMARY KEY,
    admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(admin_id, organization_id)
);
"""

# Индекс для быстрого поиска по admin_id
ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admin_organizations_admin_id ON admin_organizations(admin_id);
"""

# Индекс для быстрого поиска по organization_id
ORG_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admin_organizations_org_id ON admin_organizations(organization_id);
"""

# Удаление триггера для связей
DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_admin_organizations_updated ON admin_organizations;
"""

# Создание триггера для автоматического обновления поля updated
CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_admin_organizations_updated
    BEFORE UPDATE ON admin_organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу связей админов и организаций в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы admin_organizations...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица admin_organizations создана")
        
        # Создаем индексы (каждый отдельно)
        await db_manager.execute(ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_admin_organizations_admin_id создан")
        
        await db_manager.execute(ORG_ID_INDEX_SQL)
        logger.debug("Индекс idx_admin_organizations_org_id создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_admin_organizations_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_admin_organizations_updated создан")
        
        logger.info("Таблица admin_organizations успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы admin_organizations: {e}", exc_info=True)
        raise

