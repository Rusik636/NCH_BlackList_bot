"""
Доменная сущность обезличенного пользователя черного списка.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class BlacklistPerson:
    """
    Обезличенный пользователь в черном списке.
    Хранит хеши персональных данных.
    
    Attributes:
        id: Уникальный UUID идентификатор
        organization_id: ID организации
        hash_salt: Соль для хеширования (копия из организации)
        fio_hash: Хеш полного ФИО
        birthdate_hash: Хеш даты рождения
        passport_hash: Хеш паспорта
        department_code_hash: Хеш кода подразделения
        phone_hash: Хеш телефона
        surname_hash: Хеш фамилии (для частичного поиска)
        phone_last10_hash: Хеш последних 10 цифр телефона
        created: Дата и время создания
        updated: Дата и время последнего обновления
    """
    id: UUID
    organization_id: int
    hash_salt: str
    fio_hash: str
    birthdate_hash: str
    passport_hash: str
    department_code_hash: str
    phone_hash: str
    surname_hash: Optional[str]
    phone_last10_hash: Optional[str]
    created: datetime
    updated: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> "BlacklistPerson":
        """
        Создать объект из строки БД.
        
        Args:
            row: Словарь с данными из БД
            
        Returns:
            Экземпляр BlacklistPerson
        """
        return cls(
            id=UUID(str(row["id"])),
            organization_id=row["organization_id"],
            hash_salt=row["hash_salt"],
            fio_hash=row["fio_hash"],
            birthdate_hash=row["birthdate_hash"],
            passport_hash=row["passport_hash"],
            department_code_hash=row["department_code_hash"],
            phone_hash=row["phone_hash"],
            surname_hash=row.get("surname_hash"),
            phone_last10_hash=row.get("phone_last10_hash"),
            created=row["created"],
            updated=row["updated"],
        )

