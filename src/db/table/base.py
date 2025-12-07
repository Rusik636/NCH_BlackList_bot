"""
Базовые SQL-функции для таблиц.
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

