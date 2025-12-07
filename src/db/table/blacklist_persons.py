"""
Таблица обезличенных пользователей черного списка.
Хранит хеши персональных данных.
"""
import logging

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# Создание таблицы обезличенных пользователей
# Все персональные данные хранятся в виде хешей
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blacklist_persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Хеши персональных данных (SHA-256, hex)
    fio_hash VARCHAR(64) NOT NULL,
    birthdate_hash VARCHAR(64) NOT NULL,
    passport_hash VARCHAR(64) NOT NULL,
    department_code_hash VARCHAR(64) NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,
    
    -- Дополнительные хеши для частичного поиска
    surname_hash VARCHAR(64),
    phone_last10_hash VARCHAR(64),
    
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Уникальность по всем основным хешам в рамках организации
    UNIQUE(organization_id, fio_hash, birthdate_hash, passport_hash)
);
"""

# Индекс для поиска по организации
ORG_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_org_id 
ON blacklist_persons(organization_id);
"""

# Индекс для поиска по хешу ФИО
FIO_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_fio_hash 
ON blacklist_persons(organization_id, fio_hash);
"""

# Индекс для поиска по хешу фамилии (частичный поиск)
SURNAME_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_surname_hash 
ON blacklist_persons(organization_id, surname_hash);
"""

# Индекс для поиска по хешу телефона
PHONE_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_phone_hash 
ON blacklist_persons(organization_id, phone_hash);
"""

# Индекс для поиска по последним 10 цифрам телефона
PHONE_LAST10_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_phone_last10_hash 
ON blacklist_persons(organization_id, phone_last10_hash);
"""

# Индекс для поиска по хешу паспорта
PASSPORT_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_passport_hash 
ON blacklist_persons(organization_id, passport_hash);
"""

# Индекс для поиска по хешу даты рождения
BIRTHDATE_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_blacklist_persons_birthdate_hash 
ON blacklist_persons(organization_id, birthdate_hash);
"""

# Удаление триггера
DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_blacklist_persons_updated ON blacklist_persons;
"""

# Создание триггера для автоматического обновления поля updated
CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_blacklist_persons_updated
    BEFORE UPDATE ON blacklist_persons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу обезличенных пользователей в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы blacklist_persons...")
        
        # Создаем таблицу
        await db_manager.execute(TABLE_SQL)
        logger.debug("Таблица blacklist_persons создана")
        
        # Создаем индексы
        await db_manager.execute(ORG_ID_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_org_id создан")
        
        await db_manager.execute(FIO_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_fio_hash создан")
        
        await db_manager.execute(SURNAME_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_surname_hash создан")
        
        await db_manager.execute(PHONE_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_phone_hash создан")
        
        await db_manager.execute(PHONE_LAST10_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_phone_last10_hash создан")
        
        await db_manager.execute(PASSPORT_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_passport_hash создан")
        
        await db_manager.execute(BIRTHDATE_HASH_INDEX_SQL)
        logger.debug("Индекс idx_blacklist_persons_birthdate_hash создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_blacklist_persons_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_blacklist_persons_updated создан")
        
        logger.info("Таблица blacklist_persons успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы blacklist_persons: {e}", exc_info=True)
        raise

