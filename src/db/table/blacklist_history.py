"""
Таблица истории изменений записей черного списка.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Действия над записями
# added — добавление в ЧС
# updated — изменение записи
# deactivated — деактивация (снятие с ЧС)
# reactivated — повторная активация

# Создание таблицы истории
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blacklist_history (
    id SERIAL PRIMARY KEY,
    blacklist_record_id UUID NOT NULL REFERENCES blacklist_records(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    changed_by_admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE RESTRICT,
    old_reason TEXT,
    new_reason TEXT,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    comment TEXT,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для поиска по записи черного списка
RECORD_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_history_record_id 
ON blacklist_history(blacklist_record_id);
"""

# Индекс для поиска по админу
ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_history_admin_id 
ON blacklist_history(changed_by_admin_id);
"""

# Индекс для поиска по дате
CREATED_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_history_created 
ON blacklist_history(created);
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу истории изменений в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы blacklist_history...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица blacklist_history создана")
        
        # Создаем индексы
        await db_manager.execute(RECORD_ID_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_history_record_id создан")
        
        await db_manager.execute(ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_history_admin_id создан")
        
        await db_manager.execute(CREATED_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_history_created создан")
        
        logger.info("Таблица blacklist_history успешно создана со всеми индексами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы blacklist_history: {e}", exc_info=True)
        raise

