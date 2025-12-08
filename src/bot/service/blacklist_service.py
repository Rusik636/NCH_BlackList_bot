"""
Сервис для работы с черным списком.
Инкапсулирует бизнес-логику добавления/поиска в черном списке.

Принципы SOLID:
- SRP: Только бизнес-логика черного списка
- OCP: Расширяемость через новые методы поиска
- DIP: Зависит от абстракций (репозиториев), а не от конкретных реализаций
"""
import logging
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from src.bot.domain.organization import Organization
from src.bot.domain.blacklist_person import BlacklistPerson
from src.bot.domain.blacklist_record import BlacklistRecord, BlacklistStatus
from src.bot.domain.blacklist_history import BlacklistHistory
from src.bot.repo.organization_repository import OrganizationRepository
from src.bot.repo.blacklist_person_repository import BlacklistPersonRepository
from src.bot.repo.blacklist_record_repository import BlacklistRecordRepository
from src.bot.repo.blacklist_history_repository import BlacklistHistoryRepository
from src.bot.service.hash_service import HashService, PersonalData, PersonHashes

logger = logging.getLogger(__name__)


@dataclass
class BlacklistAddResult:
    """
    Результат добавления в черный список.
    
    Attributes:
        success: Успешность операции
        person: Обезличенный пользователь
        record: Запись в черном списке
        already_exists: Был ли пользователь уже в ЧС
        error: Сообщение об ошибке (если есть)
    """
    success: bool
    person: Optional[BlacklistPerson] = None
    record: Optional[BlacklistRecord] = None
    already_exists: bool = False
    error: Optional[str] = None


@dataclass
class BlacklistSearchResult:
    """
    Результат поиска в черном списке.
    
    Attributes:
        found: Найден ли пользователь в ЧС
        person: Обезличенный пользователь (если найден)
        records: Записи в черном списке
        active_record: Активная запись (если есть)
    """
    found: bool
    person: Optional[BlacklistPerson] = None
    records: List[BlacklistRecord] = None
    active_record: Optional[BlacklistRecord] = None
    
    def __post_init__(self):
        if self.records is None:
            self.records = []


class BlacklistService:
    """
    Сервис для работы с черным списком.
    Координирует работу репозиториев и хеш-сервиса.
    """
    
    def __init__(
        self,
        organization_repo: OrganizationRepository,
        person_repo: BlacklistPersonRepository,
        record_repo: BlacklistRecordRepository,
        history_repo: BlacklistHistoryRepository,
        hash_service: HashService,
    ):
        """
        Инициализация сервиса.
        
        Args:
            organization_repo: Репозиторий организаций
            person_repo: Репозиторий обезличенных пользователей
            record_repo: Репозиторий записей ЧС
            history_repo: Репозиторий истории
            hash_service: Сервис хеширования
        """
        self._org_repo = organization_repo
        self._person_repo = person_repo
        self._record_repo = record_repo
        self._history_repo = history_repo
        self._hash_service = hash_service
    
    async def find_existing_person_across_orgs(
        self,
        personal_data: PersonalData,
    ) -> Optional[BlacklistPerson]:
        """
        Поиск существующего пользователя по всем организациям.
        
        Алгоритм:
        1. Ищем по паспорту — если НЕ найден → новый человек
        2. Паспорт найден → проверяем код подразделения
           - Совпал → это тот же человек
           - НЕ совпал → проверяем дату рождения
             - Совпала → это тот же человек
             - НЕ совпала → новый человек
        
        Args:
            personal_data: Персональные данные для поиска
            
        Returns:
            BlacklistPerson если найден, иначе None
        """
        try:
            # Получаем все организации
            all_orgs = await self._org_repo.get_all()
            
            if not all_orgs:
                logger.debug("Нет организаций для поиска")
                return None
            
            # Для каждой организации ищем по паспорту
            for org in all_orgs:
                # Вычисляем хеш паспорта с солью этой организации
                passport_hash = self._hash_service.compute_search_hash(
                    "passport", personal_data.passport, org.hash_salt
                )
                
                # Шаг 1: Ищем по паспорту
                person = await self._person_repo.find_by_passport_hash(
                    organization_id=org.id,
                    passport_hash=passport_hash,
                )
                
                if not person:
                    # Паспорт не найден в этой организации — продолжаем поиск в других
                    continue
                
                # Паспорт найден! Теперь проверяем код подразделения
                dept_hash = self._hash_service.compute_search_hash(
                    "department_code", personal_data.department_code, org.hash_salt
                )
                
                if person.department_code_hash == dept_hash:
                    # Код подразделения совпал — это тот же человек
                    logger.info(
                        f"Найден пользователь {person.id} в org={org.id} "
                        f"(паспорт + код подразделения)"
                    )
                    return person
                
                # Код подразделения не совпал — проверяем дату рождения
                birthdate_hash = self._hash_service.compute_search_hash(
                    "birthdate", personal_data.birthdate, org.hash_salt
                )
                
                if person.birthdate_hash == birthdate_hash:
                    # Дата рождения совпала — это тот же человек
                    logger.info(
                        f"Найден пользователь {person.id} в org={org.id} "
                        f"(паспорт + дата рождения)"
                    )
                    return person
                
                # Ни код подразделения, ни дата рождения не совпали
                # Паспорт совпал, но это может быть ошибка ввода — продолжаем поиск
                logger.debug(
                    f"Паспорт совпал в org={org.id}, но код подразделения и "
                    f"дата рождения не совпали — продолжаем поиск"
                )
            
            # Не найдено ни в одной организации
            logger.debug("Пользователь не найден ни в одной организации")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при кросс-поиске пользователя: {e}", exc_info=True)
            return None
    
    async def add_to_blacklist(
        self,
        organization_id: int,
        admin_id: UUID,
        personal_data: PersonalData,
        reason: str,
        comment: Optional[str] = None,
    ) -> BlacklistAddResult:
        """
        Добавить пользователя в черный список.
        
        Если пользователь уже существует (по уникальным хешам),
        создается новая запись с новой причиной.
        
        Args:
            organization_id: ID организации
            admin_id: UUID админа, добавляющего запись
            personal_data: Персональные данные для хеширования
            reason: Причина добавления
            comment: Комментарий (опционально)
            
        Returns:
            BlacklistAddResult с результатом операции
        """
        try:
            # Получаем организацию для соли
            organization = await self._org_repo.get_by_id(organization_id)
            if not organization:
                return BlacklistAddResult(
                    success=False,
                    error=f"Организация с ID {organization_id} не найдена"
                )
            
            # Сначала ищем существующего пользователя по всем организациям
            # Алгоритм: паспорт обязателен + (код подразделения ИЛИ дата рождения)
            existing_person = await self.find_existing_person_across_orgs(
                personal_data=personal_data,
            )
            
            person: Optional[BlacklistPerson] = None
            person_created = False
            already_exists = False
            
            if existing_person:
                # Найден существующий пользователь в другой организации
                person = existing_person
                logger.info(
                    f"Найден существующий пользователь {person.id} "
                    f"из организации {person.organization_id}"
                )
                
                # Проверяем, есть ли уже активная запись для этого person
                existing_active = await self._record_repo.get_active_by_person(person.id)
                already_exists = existing_active is not None
            else:
                # Пользователь не найден — создаём нового для текущей организации
                hashes = self._hash_service.generate_hashes(
                    personal_data,
                    organization.hash_salt
                )
                
                # Проверяем, есть ли в текущей организации
                person, person_created = await self._person_repo.get_or_create(
                    organization_id,
                    hashes
                )
                
                if not person_created:
                    # Пользователь уже был в текущей организации
                    existing_active = await self._record_repo.get_active_by_person(person.id)
                    already_exists = existing_active is not None
            
            # Создаем запись в ЧС
            record = await self._record_repo.create(
                person_id=person.id,
                organization_id=organization_id,
                added_by_admin_id=admin_id,
                reason=reason,
                comment=comment,
            )
            
            # Записываем в историю
            await self._history_repo.log_added(
                blacklist_record_id=record.id,
                admin_id=admin_id,
                reason=reason,
                comment=comment,
            )
            
            logger.info(
                f"Добавлена запись в ЧС: org={organization_id}, "
                f"person={person.id}, record={record.id}, "
                f"person_created={person_created}, already_existed={already_exists}"
            )
            
            return BlacklistAddResult(
                success=True,
                person=person,
                record=record,
                already_exists=already_exists,
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении в ЧС: {e}", exc_info=True)
            return BlacklistAddResult(
                success=False,
                error=str(e)
            )
    
    async def search_by_passport(
        self,
        organization_id: int,
        passport: str,
    ) -> BlacklistSearchResult:
        """
        Поиск в черном списке по паспорту.
        
        Args:
            organization_id: ID организации
            passport: Серия и номер паспорта (10 цифр)
            
        Returns:
            BlacklistSearchResult
        """
        try:
            organization = await self._org_repo.get_by_id(organization_id)
            if not organization:
                return BlacklistSearchResult(found=False)
            
            # Вычисляем хеш паспорта
            passport_hash = self._hash_service.compute_search_hash(
                "passport",
                passport,
                organization.hash_salt
            )
            
            # Ищем пользователя
            person = await self._person_repo.find_by_passport_hash(
                organization_id,
                passport_hash
            )
            
            if not person:
                return BlacklistSearchResult(found=False)
            
            # Получаем записи
            records = await self._record_repo.get_by_person_id(person.id)
            active_record = await self._record_repo.get_active_by_person(person.id)
            
            return BlacklistSearchResult(
                found=True,
                person=person,
                records=records,
                active_record=active_record,
            )
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по паспорту: {e}", exc_info=True)
            return BlacklistSearchResult(found=False)
    
    async def search_by_phone(
        self,
        organization_id: int,
        phone: str,
    ) -> List[BlacklistSearchResult]:
        """
        Поиск в черном списке по телефону.
        Может вернуть несколько результатов.
        
        Args:
            organization_id: ID организации
            phone: Номер телефона
            
        Returns:
            Список BlacklistSearchResult
        """
        try:
            organization = await self._org_repo.get_by_id(organization_id)
            if not organization:
                return []
            
            # Вычисляем хеш телефона
            phone_hash = self._hash_service.compute_search_hash(
                "phone",
                phone,
                organization.hash_salt
            )
            
            # Ищем пользователей
            persons = await self._person_repo.find_by_phone_hash(
                organization_id,
                phone_hash
            )
            
            results = []
            for person in persons:
                records = await self._record_repo.get_by_person_id(person.id)
                active_record = await self._record_repo.get_active_by_person(person.id)
                
                results.append(BlacklistSearchResult(
                    found=True,
                    person=person,
                    records=records,
                    active_record=active_record,
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по телефону: {e}", exc_info=True)
            return []
    
    async def search_by_surname(
        self,
        organization_id: int,
        surname: str,
    ) -> List[BlacklistSearchResult]:
        """
        Поиск в черном списке по фамилии (частичный поиск).
        Может вернуть несколько результатов.
        
        Args:
            organization_id: ID организации
            surname: Фамилия
            
        Returns:
            Список BlacklistSearchResult
        """
        try:
            organization = await self._org_repo.get_by_id(organization_id)
            if not organization:
                return []
            
            # Вычисляем хеш фамилии
            surname_hash = self._hash_service.compute_search_hash(
                "surname",
                surname,
                organization.hash_salt
            )
            
            # Ищем пользователей
            persons = await self._person_repo.find_by_surname_hash(
                organization_id,
                surname_hash
            )
            
            results = []
            for person in persons:
                records = await self._record_repo.get_by_person_id(person.id)
                active_record = await self._record_repo.get_active_by_person(person.id)
                
                results.append(BlacklistSearchResult(
                    found=True,
                    person=person,
                    records=records,
                    active_record=active_record,
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по фамилии: {e}", exc_info=True)
            return []
    
    async def deactivate_record(
        self,
        record_id: UUID,
        admin_id: UUID,
        comment: Optional[str] = None,
    ) -> Optional[BlacklistRecord]:
        """
        Деактивировать запись в черном списке.
        
        Args:
            record_id: UUID записи
            admin_id: UUID админа
            comment: Причина деактивации
            
        Returns:
            Деактивированная запись или None
        """
        try:
            record = await self._record_repo.deactivate(record_id)
            
            if record:
                await self._history_repo.log_deactivated(
                    blacklist_record_id=record_id,
                    admin_id=admin_id,
                    comment=comment,
                )
                logger.info(f"Запись {record_id} деактивирована админом {admin_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Ошибка при деактивации записи {record_id}: {e}", exc_info=True)
            return None
    
    async def reactivate_record(
        self,
        record_id: UUID,
        admin_id: UUID,
        comment: Optional[str] = None,
    ) -> Optional[BlacklistRecord]:
        """
        Реактивировать запись в черном списке.
        
        Args:
            record_id: UUID записи
            admin_id: UUID админа
            comment: Причина реактивации
            
        Returns:
            Реактивированная запись или None
        """
        try:
            record = await self._record_repo.reactivate(record_id)
            
            if record:
                await self._history_repo.log_reactivated(
                    blacklist_record_id=record_id,
                    admin_id=admin_id,
                    comment=comment,
                )
                logger.info(f"Запись {record_id} реактивирована админом {admin_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Ошибка при реактивации записи {record_id}: {e}", exc_info=True)
            return None
    
    async def get_record_history(
        self,
        record_id: UUID,
    ) -> List[BlacklistHistory]:
        """
        Получить историю изменений записи.
        
        Args:
            record_id: UUID записи
            
        Returns:
            Список записей истории
        """
        return await self._history_repo.get_by_record_id(record_id)

