"""
Таблица записей черного списка.
Связывает обезличенного пользователя с причиной добавления в ЧС.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Создание таблицы записей черного списка
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blacklist_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES blacklist_persons(id) ON DELETE CASCADE,
    added_by_admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE RESTRICT,
    reason TEXT NOT NULL,
    comment TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для поиска по пользователю
PERSON_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_records_person_id ON blacklist_records(person_id);
"""

# Индекс для поиска по статусу
STATUS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_records_status ON blacklist_records(status);
"""

# Индекс для поиска по админу, добавившему запись
ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_records_admin_id ON blacklist_records(added_by_admin_id);
"""

# Удаление триггера
DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_blacklist_records_updated ON blacklist_records;
"""

# Создание триггера для автоматического обновления поля updated
CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_blacklist_records_updated
    BEFORE UPDATE ON blacklist_records
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу записей черного списка в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы blacklist_records...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица blacklist_records создана")
        
        # Создаем индексы
        await db_manager.execute(PERSON_ID_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_records_person_id создан")
        
        await db_manager.execute(STATUS_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_records_status создан")
        
        await db_manager.execute(ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_records_admin_id создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_blacklist_records_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_blacklist_records_updated создан")
        
        logger.info("Таблица blacklist_records успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы blacklist_records: {e}", exc_info=True)
        raise

