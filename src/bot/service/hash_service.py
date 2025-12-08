"""
Сервис хеширования персональных данных.
Обеспечивает обезличивание данных для хранения в черном списке.
"""
import hashlib
import logging
import re
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PersonalData:
    """
    Персональные данные для хеширования.
    
    Attributes:
        surname: Фамилия
        name: Имя
        patronymic: Отчество
        birthdate: Дата рождения (любой формат, будет приведена к ISO YYYY-MM-DD)
        passport: Серия и номер паспорта без пробела (10 цифр)
        department_code: Код подразделения (6 цифр)
        phone: Номер телефона
    """
    surname: str
    name: str
    patronymic: str
    birthdate: str  # Любой формат → ISO (YYYY-MM-DD)
    passport: str
    department_code: str
    phone: str


@dataclass
class PersonHashes:
    """
    Хеши персональных данных для хранения в БД.
    
    Attributes:
        fio_hash: Хеш полного ФИО
        surname_hash: Хеш только фамилии (для частичного поиска)
        birthdate_hash: Хеш даты рождения
        passport_hash: Хеш паспорта
        department_code_hash: Хеш кода подразделения
        phone_hash: Хеш полного телефона
        phone_last10_hash: Хеш последних 10 цифр телефона (для частичного поиска)
    """
    fio_hash: str
    surname_hash: str
    birthdate_hash: str
    passport_hash: str
    department_code_hash: str
    phone_hash: str
    phone_last10_hash: str


class HashService:
    """Сервис для хеширования персональных данных."""
    
    def __init__(self, pepper: str):
        """
        Инициализация сервиса хеширования.
        
        Args:
            pepper: Глобальный секретный ключ (pepper) из конфигурации
        """
        self._pepper = pepper
    
    def _normalize_text(self, text: str) -> str:
        """
        Нормализация текста перед хешированием.
        Приводит к нижнему регистру, убирает лишние пробелы.
        
        Args:
            text: Исходный текст
            
        Returns:
            Нормализованный текст
        """
        return " ".join(text.lower().strip().split())
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Нормализация номера телефона к формату +79991234567.
        
        Args:
            phone: Исходный номер телефона
            
        Returns:
            Нормализованный номер в формате +79991234567
        """
        # Удаляем все нецифровые символы кроме +
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Если есть +, убираем его для обработки
        has_plus = digits.startswith('+')
        if has_plus:
            digits = digits[1:]
        
        # Нормализация российских номеров
        if len(digits) == 11:
            # Формат 8XXXXXXXXXX или 7XXXXXXXXXX → 7XXXXXXXXXX
            if digits[0] == '8':
                digits = '7' + digits[1:]
            elif digits[0] != '7':
                digits = '7' + digits
        elif len(digits) == 10:
            # Формат XXXXXXXXXX → 7XXXXXXXXXX
            digits = '7' + digits
        elif len(digits) == 12:
            # Формат 7XXXXXXXXXXX → берем последние 11 цифр
            if digits.startswith('7'):
                digits = digits[:11]
            else:
                digits = '7' + digits[1:]
        
        # Возвращаем в формате +79991234567
        return '+' + digits
    
    def _normalize_date(self, date: str) -> str:
        """
        Нормализация даты рождения к формату ISO (YYYY-MM-DD).
        
        Поддерживаемые входные форматы:
            - DD.MM.YYYY (01.12.1990)
            - DD/MM/YYYY (01/12/1990)
            - DD-MM-YYYY (01-12-1990)
            - YYYY-MM-DD (1990-12-01) — уже ISO
            - YYYY/MM/DD (1990/12/01)
        
        Args:
            date: Дата в любом поддерживаемом формате
            
        Returns:
            Дата в формате ISO: YYYY-MM-DD
            
        Raises:
            ValueError: Если формат даты не распознан
        """
        date = date.strip()
        
        # Разделяем по любому из разделителей
        if '.' in date:
            parts = date.split('.')
        elif '/' in date:
            parts = date.split('/')
        elif '-' in date:
            parts = date.split('-')
        else:
            raise ValueError(f"Неизвестный формат даты: {date}")
        
        if len(parts) != 3:
            raise ValueError(f"Неверный формат даты: {date}")
        
        # Определяем порядок: если первая часть > 31 — это год (YYYY-MM-DD)
        # Иначе — это день (DD.MM.YYYY)
        first_part = int(parts[0])
        
        if first_part > 31:
            # Формат YYYY-MM-DD или YYYY/MM/DD
            year, month, day = parts[0], parts[1], parts[2]
        else:
            # Формат DD.MM.YYYY или DD/MM/YYYY или DD-MM-YYYY
            day, month, year = parts[0], parts[1], parts[2]
        
        # Приводим к единому виду с ведущими нулями
        year = str(int(year)).zfill(4)
        month = str(int(month)).zfill(2)
        day = str(int(day)).zfill(2)
        
        return f"{year}-{month}-{day}"
    
    def _compute_hash(self, data: str, salt: str) -> str:
        """
        Вычислить SHA-256 хеш от данных с солью и pepper.
        
        Args:
            data: Данные для хеширования
            salt: Соль организации
            
        Returns:
            Хеш в hex-формате (64 символа)
        """
        # Формат: данные + соль организации + глобальный pepper
        combined = f"{data}{salt}{self._pepper}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def generate_hashes(self, data: PersonalData, org_salt: str) -> PersonHashes:
        """
        Генерировать все хеши для персональных данных.
        
        Args:
            data: Персональные данные
            org_salt: Соль организации
            
        Returns:
            PersonHashes с хешами всех полей
        """
        # Нормализация данных
        surname = self._normalize_text(data.surname)
        name = self._normalize_text(data.name)
        patronymic = self._normalize_text(data.patronymic)
        birthdate = self._normalize_date(data.birthdate)
        # Паспорт и код подразделения - только цифры
        passport = re.sub(r'\D', '', data.passport)
        department_code = re.sub(r'\D', '', data.department_code)
        # Телефон - формат +79991234567
        phone = self._normalize_phone(data.phone)
        
        # Полное ФИО
        fio = f"{surname} {name} {patronymic}"
        
        # Последние 10 цифр телефона (без +7)
        # Для +79991234567 берем 9991234567
        phone_last10 = phone[-10:] if len(phone) >= 12 else phone
        
        return PersonHashes(
            fio_hash=self._compute_hash(fio, org_salt),
            surname_hash=self._compute_hash(surname, org_salt),
            birthdate_hash=self._compute_hash(birthdate, org_salt),
            passport_hash=self._compute_hash(passport, org_salt),
            department_code_hash=self._compute_hash(department_code, org_salt),
            phone_hash=self._compute_hash(phone, org_salt),
            phone_last10_hash=self._compute_hash(phone_last10, org_salt),
        )
    
    def compute_search_hash(
        self, 
        field: str, 
        value: str, 
        org_salt: str
    ) -> str:
        """
        Вычислить хеш для поиска по конкретному полю.
        
        Args:
            field: Название поля (fio, surname, birthdate, passport, 
                   department_code, phone, phone_last10)
            value: Значение для поиска
            org_salt: Соль организации
            
        Returns:
            Хеш для поиска
        """
        # Нормализуем значение в зависимости от поля
        if field in ['fio', 'surname']:
            normalized = self._normalize_text(value)
        elif field == 'birthdate':
            normalized = self._normalize_date(value)
        elif field == 'passport':
            # Паспорт - только цифры
            normalized = re.sub(r'\D', '', value)
        elif field == 'department_code':
            # Код подразделения - только цифры
            normalized = re.sub(r'\D', '', value)
        elif field == 'phone':
            # Телефон - формат +79991234567
            normalized = self._normalize_phone(value)
        elif field == 'phone_last10':
            # Последние 10 цифр телефона (без +7)
            normalized_phone = self._normalize_phone(value)
            normalized = normalized_phone[-10:] if len(normalized_phone) >= 12 else normalized_phone
        else:
            normalized = value
        
        return self._compute_hash(normalized, org_salt)
    
    def compute_fio_hash(
        self, 
        surname: str, 
        name: str, 
        patronymic: str, 
        org_salt: str
    ) -> str:
        """
        Вычислить хеш ФИО из отдельных компонентов.
        
        Args:
            surname: Фамилия
            name: Имя
            patronymic: Отчество
            org_salt: Соль организации
            
        Returns:
            Хеш ФИО
        """
        fio = f"{self._normalize_text(surname)} {self._normalize_text(name)} {self._normalize_text(patronymic)}"
        return self._compute_hash(fio, org_salt)
