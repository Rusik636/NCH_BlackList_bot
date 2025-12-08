"""
Парсер входных данных для проверки в черном списке.
Распознаёт ФИО, паспорт, телефон, дату рождения, код подразделения.
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedSearchData:
    """
    Распарсенные данные для поиска.
    
    Attributes:
        fio: ФИО (приведено к нижнему регистру)
        passport: Серия и номер паспорта (10 цифр, без пробела)
        birthdate: Дата рождения (ISO формат YYYY-MM-DD)
        department_code: Код подразделения (6 цифр)
        phone: Номер телефона (нормализованный)
    """
    fio: Optional[str] = None
    passport: Optional[str] = None
    birthdate: Optional[str] = None
    department_code: Optional[str] = None
    phone: Optional[str] = None


class SearchDataParser:
    """
    Парсер данных для поиска в черном списке.
    Распознаёт данные из многострочного текста.
    """
    
    # Паттерн для даты (ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ)
    DATE_PATTERN = re.compile(
        r'^(\d{2})[./-](\d{2})[./-](\d{4})$'
    )
    
    # Паттерн для паспорта (10 цифр подряд или 4+пробел+6)
    PASSPORT_PATTERN = re.compile(
        r'^(\d{4})\s*(\d{6})$'
    )
    
    # Паттерн для кода подразделения (6 цифр или XXX-XXX)
    DEPT_CODE_PATTERN = re.compile(
        r'^(\d{3})[-\s]?(\d{3})$'
    )
    
    # Паттерны для телефона
    PHONE_PATTERNS = [
        re.compile(r'^\+7\d{10}$'),           # +79991234567
        re.compile(r'^8\d{10}$'),              # 89991234567
        re.compile(r'^7\d{10}$'),              # 79991234567
        re.compile(r'^\+7[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$'),  # +7 (999) 123-45-67
        re.compile(r'^8[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$'),    # 8 (999) 123-45-67
    ]
    
    # Паттерн для ФИО (3 слова, только буквы и дефисы)
    FIO_PATTERN = re.compile(
        r'^[a-zA-Zа-яА-ЯёЁ\-]+\s+[a-zA-Zа-яА-ЯёЁ\-]+\s+[a-zA-Zа-яА-ЯёЁ\-]+$'
    )
    
    @classmethod
    def parse(cls, text: str) -> ParsedSearchData:
        """
        Распарсить многострочный текст и распознать данные.
        
        Args:
            text: Многострочный текст с данными
            
        Returns:
            ParsedSearchData с распознанными полями
        """
        result = ParsedSearchData()
        
        # Разбиваем по строкам
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        for line in lines:
            # Пробуем распознать каждую строку
            if not result.passport and cls._is_passport(line):
                result.passport = cls._normalize_passport(line)
                logger.debug(f"Распознан паспорт: {result.passport}")
                continue
            
            if not result.department_code and cls._is_department_code(line):
                result.department_code = cls._normalize_department_code(line)
                logger.debug(f"Распознан код подразделения: {result.department_code}")
                continue
            
            if not result.birthdate and cls._is_date(line):
                result.birthdate = cls._normalize_date(line)
                logger.debug(f"Распознана дата рождения: {result.birthdate}")
                continue
            
            if not result.phone and cls._is_phone(line):
                result.phone = cls._normalize_phone(line)
                logger.debug(f"Распознан телефон: {result.phone}")
                continue
            
            if not result.fio and cls._is_fio(line):
                result.fio = cls._normalize_fio(line)
                logger.debug(f"Распознано ФИО: {result.fio}")
                continue
        
        return result
    
    @classmethod
    def _is_passport(cls, text: str) -> bool:
        """Проверяет, является ли текст паспортными данными."""
        # Удаляем все нецифровые символы для проверки
        digits = re.sub(r'\D', '', text)
        if len(digits) == 10:
            # Дополнительная проверка: серия не начинается с 0
            if not digits.startswith('0'):
                return True
        return bool(cls.PASSPORT_PATTERN.match(text))
    
    @classmethod
    def _normalize_passport(cls, text: str) -> str:
        """Нормализует паспорт к 10 цифрам."""
        return re.sub(r'\D', '', text)
    
    @classmethod
    def _is_department_code(cls, text: str) -> bool:
        """Проверяет, является ли текст кодом подразделения."""
        digits = re.sub(r'\D', '', text)
        # 6 цифр и не похоже на другие данные
        if len(digits) == 6:
            # Исключаем случай, когда это часть паспорта
            return bool(cls.DEPT_CODE_PATTERN.match(text)) or digits == text
        return False
    
    @classmethod
    def _normalize_department_code(cls, text: str) -> str:
        """Нормализует код подразделения к 6 цифрам."""
        return re.sub(r'\D', '', text)
    
    @classmethod
    def _is_date(cls, text: str) -> bool:
        """Проверяет, является ли текст датой рождения."""
        return bool(cls.DATE_PATTERN.match(text))
    
    @classmethod
    def _normalize_date(cls, text: str) -> str:
        """Нормализует дату к ISO формату YYYY-MM-DD."""
        match = cls.DATE_PATTERN.match(text)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}"
        return text
    
    @classmethod
    def _is_phone(cls, text: str) -> bool:
        """Проверяет, является ли текст номером телефона."""
        # Удаляем все нецифровые кроме +
        clean = re.sub(r'[^\d+]', '', text)
        
        # Начинается с +7, 8, 7 и содержит 11 цифр
        if clean.startswith('+7') and len(clean) == 12:
            return True
        if clean.startswith('8') and len(clean) == 11:
            return True
        if clean.startswith('7') and len(clean) == 11:
            return True
        
        # Проверяем по паттернам
        for pattern in cls.PHONE_PATTERNS:
            if pattern.match(text):
                return True
        
        return False
    
    @classmethod
    def _normalize_phone(cls, text: str) -> str:
        """
        Нормализует телефон к формату +7XXXXXXXXXX.
        """
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', text)
        
        # Если начинается с 8, меняем на 7
        if len(digits) == 11 and digits.startswith('8'):
            digits = '7' + digits[1:]
        
        # Если 10 цифр, добавляем 7
        if len(digits) == 10:
            digits = '7' + digits
        
        return '+' + digits if digits else text
    
    @classmethod
    def _is_fio(cls, text: str) -> bool:
        """Проверяет, является ли текст ФИО (3 слова)."""
        # Удаляем лишние пробелы
        cleaned = ' '.join(text.split())
        parts = cleaned.split()
        
        if len(parts) != 3:
            return False
        
        # Каждая часть должна содержать только буквы и дефис
        for part in parts:
            if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\-]{2,}$', part):
                return False
        
        return True
    
    @classmethod
    def _normalize_fio(cls, text: str) -> str:
        """Нормализует ФИО: приводит к нижнему регистру, убирает лишние пробелы."""
        cleaned = ' '.join(text.split())
        return cleaned.lower()

