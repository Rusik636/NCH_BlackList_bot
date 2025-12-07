"""
Определения таблиц базы данных.
Содержит SQL схемы для создания таблиц и функции инициализации.
"""
import logging
from typing import Optional

from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# SQL схема для таблицы админов
# Примечание: gen_random_uuid() доступен в PostgreSQL 13+ по умолчанию.
# Для более старых версий может потребоваться расширение: CREATE EXTENSION IF NOT EXISTS pgcrypto;

# Создание таблицы (отдельный запрос)
ADMINS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id BIGINT NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для быстрого поиска по Telegram ID (отдельный запрос)
ADMINS_ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admins_admin_id ON admins(admin_id);
"""

# Индекс для поиска по роли (отдельный запрос)
ADMINS_ROLE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
"""


# Функция для автоматического обновления поля updated
UPDATE_TIMESTAMP_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION update_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


# Удаление триггера (отдельный запрос)
ADMINS_DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_admins_updated ON admins;
"""

# Создание триггера для автоматического обновления поля updated (отдельный запрос)
ADMINS_CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_admins_updated
    BEFORE UPDATE ON admins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


# SQL схема для таблицы организаций

# Создание таблицы организаций (отдельный запрос)
ORGANIZATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Индекс для быстрого поиска по названию организации (отдельный запрос)
ORGANIZATIONS_NAME_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);
"""

# Удаление триггера для организаций (отдельный запрос)
ORGANIZATIONS_DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_organizations_updated ON organizations;
"""

# Создание триггера для автоматического обновления поля updated (отдельный запрос)
ORGANIZATIONS_CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_organizations_updated
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


# SQL схема для таблицы связей админов и организаций

# Создание таблицы связей (отдельный запрос)
ADMIN_ORGANIZATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admin_organizations (
    id SERIAL PRIMARY KEY,
    admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(admin_id, organization_id)
);
"""

# Индекс для быстрого поиска по admin_id (отдельный запрос)
ADMIN_ORGANIZATIONS_ADMIN_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admin_organizations_admin_id ON admin_organizations(admin_id);
"""

# Индекс для быстрого поиска по organization_id (отдельный запрос)
ADMIN_ORGANIZATIONS_ORG_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_admin_organizations_org_id ON admin_organizations(organization_id);
"""

# Удаление триггера для связей (отдельный запрос)
ADMIN_ORGANIZATIONS_DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS update_admin_organizations_updated ON admin_organizations;
"""

# Создание триггера для автоматического обновления поля updated (отдельный запрос)
ADMIN_ORGANIZATIONS_CREATE_TRIGGER_SQL = """
CREATE TRIGGER update_admin_organizations_updated
    BEFORE UPDATE ON admin_organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_column();
"""


async def create_admins_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу админов в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы admins...")
        
        # Создаем таблицу
        await db_manager.execute(ADMINS_TABLE_SQL)
        logger.debug("Таблица admins создана")
        
        # Создаем индексы (каждый отдельно)
        await db_manager.execute(ADMINS_ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_admins_admin_id создан")
        
        await db_manager.execute(ADMINS_ROLE_INDEX_SQL)
        logger.debug("Индекс idx_admins_role создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(ADMINS_DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_admins_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(ADMINS_CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_admins_updated создан")
        
        logger.info("Таблица admins успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы admins: {e}", exc_info=True)
        raise


async def create_organizations_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу организаций в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы organizations...")
        
        # Создаем таблицу
        await db_manager.execute(ORGANIZATIONS_TABLE_SQL)
        logger.debug("Таблица organizations создана")
        
        # Создаем индекс для поиска по названию
        await db_manager.execute(ORGANIZATIONS_NAME_INDEX_SQL)
        logger.debug("Индекс idx_organizations_name создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(ORGANIZATIONS_DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_organizations_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(ORGANIZATIONS_CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_organizations_updated создан")
        
        logger.info("Таблица organizations успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы organizations: {e}", exc_info=True)
        raise


async def create_admin_organizations_table(db_manager: DatabaseManager) -> None:
    """
    Создать таблицу связей админов и организаций в базе данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Создание таблицы admin_organizations...")
        
        # Создаем таблицу
        await db_manager.execute(ADMIN_ORGANIZATIONS_TABLE_SQL)
        logger.debug("Таблица admin_organizations создана")
        
        # Создаем индексы (каждый отдельно)
        await db_manager.execute(ADMIN_ORGANIZATIONS_ADMIN_ID_INDEX_SQL)
        logger.debug("Индекс idx_admin_organizations_admin_id создан")
        
        await db_manager.execute(ADMIN_ORGANIZATIONS_ORG_ID_INDEX_SQL)
        logger.debug("Индекс idx_admin_organizations_org_id создан")
        
        # Удаляем триггер, если существует (для идемпотентности)
        await db_manager.execute(ADMIN_ORGANIZATIONS_DROP_TRIGGER_SQL)
        logger.debug("Старый триггер update_admin_organizations_updated удален (если существовал)")
        
        # Создаем триггер для автоматического обновления updated
        await db_manager.execute(ADMIN_ORGANIZATIONS_CREATE_TRIGGER_SQL)
        logger.debug("Триггер update_admin_organizations_updated создан")
        
        logger.info("Таблица admin_organizations успешно создана со всеми индексами и триггерами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы admin_organizations: {e}", exc_info=True)
        raise


async def initialize_tables(db_manager: DatabaseManager) -> None:
    """
    Инициализировать все таблицы базы данных.
    
    Args:
        db_manager: Менеджер подключения к базе данных
    """
    try:
        logger.info("Инициализация таблиц базы данных...")
        
        # Создаем функцию для обновления timestamp (нужна для всех таблиц)
        await db_manager.execute(UPDATE_TIMESTAMP_FUNCTION_SQL)
        logger.debug("Функция update_updated_column создана")
        
        # Создаем таблицу админов
        await create_admins_table(db_manager)
        
        # Создаем таблицу организаций
        await create_organizations_table(db_manager)
        
        # Создаем таблицу связей админов и организаций (после создания основных таблиц)
        await create_admin_organizations_table(db_manager)
        
        logger.info("Все таблицы успешно инициализированы")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации таблиц: {e}", exc_info=True)
        raise

