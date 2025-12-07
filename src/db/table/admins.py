"""
Таблица администраторов.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Создание таблицы
# Примечание: gen_random_uuid() доступен в PostgreSQL 13+ по умолчанию.
# Для более старых версий может потребоваться расширение: CREATE EXTENSION IF NOT EXISTS pgcrypto;
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id BIGINT NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для быстрого поиска по Telegram ID
ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admins_admin_id ON admins(admin_id);
"""

# Индекс для поиска по роли
ROLE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
"""

# Удаление триггера
DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_admins_updated ON admins;
"""

# Создание триггера для автоматического обновления поля updated
CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_admins_updated
    BEFORE UPDATE ON admins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу админов в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы admins...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица admins создана")
        
        # Создаем индексы (каждый отдельно)
        await db_manager.execute(ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_admins_admin_id создан")
        
        await db_manager.execute(ROLE_INDEX_SQL)
        logger.debug("Индекс idx_admins_role создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_admins_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_admins_updated создан")
        
        logger.info("Таблица admins успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы admins: {e}", exc_info=True)
        raise

