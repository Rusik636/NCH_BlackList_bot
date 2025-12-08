"""
Репозиторий для работы с обезличенными пользователями черного списка.
Принцип единственной ответственности (SRP): только CRUD операции с blacklist_persons.
"""
import logging
from typing import Optional, List
from uuid import UUID

from src.db.connection import DatabaseManager
from src.bot.domain.blacklist_person import BlacklistPerson
from src.bot.service.hash_service import PersonHashes

logger = logging.getLogger(__name__)


class BlacklistPersonRepository:
    """
    Репозиторий для работы с таблицей blacklist_persons.
    
    Responsibilities:
        - CRUD операции с обезличенными пользователями
        - Поиск по хешам персональных данных
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация репозитория.
        
        Args:
            db_manager: Менеджер подключения к БД
        """
        self._db = db_manager
    
    async def create(
        self,
        organization_id: int,
        hash_salt: str,
        hashes: PersonHashes,
    ) -> BlacklistPerson:
        """
        Создать запись обезличенного пользователя.
        
        Args:
            organization_id: ID организации
            hash_salt: Соль организации для хеширования
            hashes: Хеши персональных данных
            
        Returns:
            Созданный BlacklistPerson
            
        Raises:
            Exception: При ошибке создания
        """
        try:
            query = """
                INSERT INTO blacklist_persons (
                    organization_id,
                    hash_salt,
                    fio_hash,
                    birthdate_hash,
                    passport_hash,
                    department_code_hash,
                    phone_hash,
                    surname_hash,
                    phone_last10_hash
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """
            
            row = await self._db.fetchrow(
                query,
                organization_id,
                hash_salt,
                hashes.fio_hash,
                hashes.birthdate_hash,
                hashes.passport_hash,
                hashes.department_code_hash,
                hashes.phone_hash,
                hashes.surname_hash,
                hashes.phone_last10_hash,
            )
            
            if not row:
                raise ValueError("Не удалось создать запись пользователя")
            
            person = BlacklistPerson.from_db_row(row)
            logger.info(f"Создан обезличенный пользователь: {person.id}")
            
            return person
            
        except Exception as e:
            logger.error(f"Ошибка при создании обезличенного пользователя: {e}", exc_info=True)
            raise
    
    async def get_by_id(self, person_id: UUID) -> Optional[BlacklistPerson]:
        """
        Получить пользователя по ID.
        
        Args:
            person_id: UUID пользователя
            
        Returns:
            BlacklistPerson или None
        """
        try:
            query = "SELECT * FROM blacklist_persons WHERE id = $1"
            row = await self._db.fetchrow(query, person_id)
            
            if row:
                return BlacklistPerson.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {person_id}: {e}", exc_info=True)
            raise
    
    async def find_by_passport_hash(
        self,
        organization_id: int,
        passport_hash: str,
    ) -> Optional[BlacklistPerson]:
        """
        Найти пользователя по хешу паспорта в организации.
        
        Args:
            organization_id: ID организации
            passport_hash: Хеш паспорта
            
        Returns:
            BlacklistPerson или None
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1 AND passport_hash = $2
            """
            
            row = await self._db.fetchrow(query, organization_id, passport_hash)
            
            if row:
                return BlacklistPerson.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по паспорту: {e}", exc_info=True)
            raise
    
    async def find_by_fio_hash(
        self,
        organization_id: int,
        fio_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти пользователей по хешу ФИО в организации.
        
        Args:
            organization_id: ID организации
            fio_hash: Хеш ФИО
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1 AND fio_hash = $2
            """
            
            rows = await self._db.fetch(query, organization_id, fio_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по ФИО: {e}", exc_info=True)
            raise
    
    async def find_by_surname_hash(
        self,
        organization_id: int,
        surname_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти пользователей по хешу фамилии (частичный поиск).
        
        Args:
            organization_id: ID организации
            surname_hash: Хеш фамилии
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1 AND surname_hash = $2
            """
            
            rows = await self._db.fetch(query, organization_id, surname_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по фамилии: {e}", exc_info=True)
            raise
    
    async def find_by_phone_hash(
        self,
        organization_id: int,
        phone_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти пользователей по хешу телефона.
        
        Args:
            organization_id: ID организации
            phone_hash: Хеш телефона
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1 AND phone_hash = $2
            """
            
            rows = await self._db.fetch(query, organization_id, phone_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по телефону: {e}", exc_info=True)
            raise
    
    async def find_by_phone_last10_hash(
        self,
        organization_id: int,
        phone_last10_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти пользователей по хешу последних 10 цифр телефона.
        
        Args:
            organization_id: ID организации
            phone_last10_hash: Хеш последних 10 цифр
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1 AND phone_last10_hash = $2
            """
            
            rows = await self._db.fetch(query, organization_id, phone_last10_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по телефону (last10): {e}", exc_info=True)
            raise
    
    async def find_existing(
        self,
        organization_id: int,
        hashes: PersonHashes,
    ) -> Optional[BlacklistPerson]:
        """
        Найти существующего пользователя по уникальному набору хешей.
        Уникальность определяется по: organization_id + fio_hash + birthdate_hash + passport_hash
        
        Args:
            organization_id: ID организации
            hashes: Хеши персональных данных
            
        Returns:
            BlacklistPerson или None
        """
        try:
            query = """
                SELECT * FROM blacklist_persons
                WHERE organization_id = $1
                  AND fio_hash = $2
                  AND birthdate_hash = $3
                  AND passport_hash = $4
            """
            
            row = await self._db.fetchrow(
                query,
                organization_id,
                hashes.fio_hash,
                hashes.birthdate_hash,
                hashes.passport_hash,
            )
            
            if row:
                return BlacklistPerson.from_db_row(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске существующего пользователя: {e}", exc_info=True)
            raise
    
    async def get_or_create(
        self,
        organization_id: int,
        hash_salt: str,
        hashes: PersonHashes,
    ) -> tuple[BlacklistPerson, bool]:
        """
        Получить существующего пользователя или создать нового.
        
        Args:
            organization_id: ID организации
            hash_salt: Соль организации
            hashes: Хеши персональных данных
            
        Returns:
            Tuple (BlacklistPerson, created: bool)
        """
        existing = await self.find_existing(organization_id, hashes)
        
        if existing:
            return existing, False
        
        person = await self.create(organization_id, hash_salt, hashes)
        return person, True
    
    async def delete(self, person_id: UUID) -> bool:
        """
        Удалить обезличенного пользователя.
        
        Args:
            person_id: UUID пользователя
            
        Returns:
            True если удален
        """
        try:
            query = "DELETE FROM blacklist_persons WHERE id = $1 RETURNING id"
            row = await self._db.fetchrow(query, person_id)
            
            if row:
                logger.info(f"Удален обезличенный пользователь: {person_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {person_id}: {e}", exc_info=True)
            raise
    
    async def find_by_hashes_with_match_count(
        self,
        passport_hash: str,
        department_code_hash: str,
        birthdate_hash: str,
        organization_id: int,
    ) -> Optional[tuple[BlacklistPerson, int]]:
        """
        Найти пользователя по хешам с подсчётом количества совпадений.
        Поиск в рамках одной организации.
        
        Args:
            passport_hash: Хеш паспорта
            department_code_hash: Хеш кода подразделения
            birthdate_hash: Хеш даты рождения
            organization_id: ID организации
            
        Returns:
            Tuple (BlacklistPerson, match_count) или None
            match_count: количество совпавших полей (1-3)
        """
        try:
            query = """
                SELECT *,
                    (CASE WHEN passport_hash = $1 THEN 1 ELSE 0 END +
                     CASE WHEN department_code_hash = $2 THEN 1 ELSE 0 END +
                     CASE WHEN birthdate_hash = $3 THEN 1 ELSE 0 END) as match_count
                FROM blacklist_persons
                WHERE organization_id = $4
                  AND (passport_hash = $1 
                       OR department_code_hash = $2 
                       OR birthdate_hash = $3)
                ORDER BY match_count DESC
                LIMIT 1
            """
            
            row = await self._db.fetchrow(
                query,
                passport_hash,
                department_code_hash,
                birthdate_hash,
                organization_id,
            )
            
            if row:
                match_count = row["match_count"]
                person = BlacklistPerson.from_db_row(row)
                return person, match_count
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по хешам: {e}", exc_info=True)
            raise
    
    async def get_unique_salts(self) -> List[str]:
        """
        Получить список уникальных солей из всех записей.
        Оптимизация: вместо перебора всех организаций,
        получаем только соли, которые реально используются.
        
        Returns:
            Список уникальных солей
        """
        try:
            query = "SELECT DISTINCT hash_salt FROM blacklist_persons"
            rows = await self._db.fetch(query)
            return [row["hash_salt"] for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при получении уникальных солей: {e}", exc_info=True)
            raise
    
    async def find_by_passport_hash_global(
        self,
        passport_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти всех пользователей по хешу паспорта (глобальный поиск).
        
        Args:
            passport_hash: Хеш паспорта
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = "SELECT * FROM blacklist_persons WHERE passport_hash = $1"
            rows = await self._db.fetch(query, passport_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при глобальном поиске по паспорту: {e}", exc_info=True)
            raise
    
    async def find_by_fio_hash_global(
        self,
        fio_hash: str,
    ) -> List[BlacklistPerson]:
        """
        Найти всех пользователей по хешу ФИО (глобальный поиск).
        
        Args:
            fio_hash: Хеш ФИО
            
        Returns:
            Список найденных пользователей
        """
        try:
            query = "SELECT * FROM blacklist_persons WHERE fio_hash = $1"
            rows = await self._db.fetch(query, fio_hash)
            return [BlacklistPerson.from_db_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Ошибка при глобальном поиске по ФИО: {e}", exc_info=True)
            raise

