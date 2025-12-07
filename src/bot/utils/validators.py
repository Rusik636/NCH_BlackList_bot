"""
Утилиты валидации персональных данных.
Проверка корректности ФИО, даты, паспортных данных, телефона, кода подразделения.
"""
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ValidationResult:
    """
    Результат валидации.
    
    Attributes:
        is_valid: Прошла ли валидация
        error: Сообщение об ошибке (если не прошла)
        normalized: Нормализованное значение (если прошла)
    """
    is_valid: bool
    error: Optional[str] = None
    normalized: Optional[str] = None


class Validators:
    """Класс с методами валидации персональных данных."""
    
    # =========================================================================
    # ФИО
    # =========================================================================
    
    @staticmethod
    def validate_fio(fio: str) -> ValidationResult:
        """
        Валидация ФИО (Фамилия Имя Отчество).
        
        Правила:
        - Минимум 3 слова (Фамилия, Имя, Отчество)
        - Каждое слово минимум 2 символа
        - Только буквы (кириллица/латиница) и дефис
        - Первая буква каждого слова — заглавная
        
        Args:
            fio: Строка с ФИО
            
        Returns:
            ValidationResult с результатом проверки
        """
        if not fio or not fio.strip():
            return ValidationResult(False, "ФИО не может быть пустым")
        
        # Убираем лишние пробелы
        fio = " ".join(fio.strip().split())
        parts = fio.split()
        
        if len(parts) < 3:
            return ValidationResult(
                False, 
                "ФИО должно содержать минимум 3 слова (Фамилия Имя Отчество)"
            )
        
        # Паттерн для слова: буквы (кириллица/латиница) и дефис
        word_pattern = re.compile(r'^[а-яёА-ЯЁa-zA-Z-]+$')
        
        normalized_parts = []
        for i, part in enumerate(parts):
            if len(part) < 2:
                position = ["Фамилия", "Имя", "Отчество"][i] if i < 3 else f"Слово {i+1}"
                return ValidationResult(
                    False, 
                    f"{position} должно содержать минимум 2 символа"
                )
            
            if not word_pattern.match(part):
                return ValidationResult(
                    False, 
                    f"'{part}' содержит недопустимые символы. Разрешены только буквы и дефис"
                )
            
            # Нормализация: первая буква заглавная
            normalized_parts.append(part.capitalize())
        
        normalized = " ".join(normalized_parts)
        return ValidationResult(True, normalized=normalized)
    
    # =========================================================================
    # Дата рождения
    # =========================================================================
    
    @staticmethod
    def validate_birthdate(date_str: str) -> ValidationResult:
        """
        Валидация даты рождения.
        
        Поддерживаемые форматы:
        - DD.MM.YYYY (01.12.1990)
        - DD/MM/YYYY (01/12/1990)
        - DD-MM-YYYY (01-12-1990)
        - YYYY-MM-DD (1990-12-01)
        
        Правила:
        - Дата должна быть валидной
        - Возраст от 14 до 120 лет
        
        Args:
            date_str: Строка с датой
            
        Returns:
            ValidationResult с результатом и датой в формате ISO (YYYY-MM-DD)
        """
        if not date_str or not date_str.strip():
            return ValidationResult(False, "Дата рождения не может быть пустой")
        
        date_str = date_str.strip()
        
        # Определяем формат и парсим дату
        formats = [
            (r'^(\d{2})\.(\d{2})\.(\d{4})$', 'dmy'),  # DD.MM.YYYY
            (r'^(\d{2})/(\d{2})/(\d{4})$', 'dmy'),    # DD/MM/YYYY
            (r'^(\d{2})-(\d{2})-(\d{4})$', 'dmy'),    # DD-MM-YYYY
            (r'^(\d{4})-(\d{2})-(\d{2})$', 'ymd'),    # YYYY-MM-DD
            (r'^(\d{4})/(\d{2})/(\d{2})$', 'ymd'),    # YYYY/MM/DD
        ]
        
        day, month, year = None, None, None
        
        for pattern, order in formats:
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                if order == 'dmy':
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # ymd
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                break
        
        if day is None:
            return ValidationResult(
                False, 
                "Неверный формат даты. Используйте ДД.ММ.ГГГГ"
            )
        
        # Проверяем валидность даты
        try:
            birth_date = datetime(year, month, day)
        except ValueError:
            return ValidationResult(False, "Указана несуществующая дата")
        
        # Проверяем возраст
        today = datetime.now()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        if age < 14:
            return ValidationResult(False, "Возраст должен быть не менее 14 лет")
        
        if age > 120:
            return ValidationResult(False, "Указана некорректная дата рождения")
        
        if birth_date > today:
            return ValidationResult(False, "Дата рождения не может быть в будущем")
        
        # Нормализуем в ISO формат
        normalized = f"{year:04d}-{month:02d}-{day:02d}"
        return ValidationResult(True, normalized=normalized)
    
    # =========================================================================
    # Паспортные данные
    # =========================================================================
    
    @staticmethod
    def validate_passport(passport: str) -> ValidationResult:
        """
        Валидация паспортных данных РФ (серия и номер).
        
        Правила:
        - Ровно 10 цифр (4 серия + 6 номер)
        - Пробелы и другие символы игнорируются
        
        Args:
            passport: Строка с серией и номером паспорта
            
        Returns:
            ValidationResult с результатом и нормализованным значением (только цифры)
        """
        if not passport or not passport.strip():
            return ValidationResult(False, "Паспортные данные не могут быть пустыми")
        
        # Оставляем только цифры
        digits = re.sub(r'\D', '', passport)
        
        if len(digits) != 10:
            return ValidationResult(
                False, 
                f"Паспорт должен содержать 10 цифр (серия 4 + номер 6). "
                f"Введено: {len(digits)} цифр"
            )
        
        # Проверяем, что серия не начинается с 0
        series = digits[:4]
        if series[0] == '0':
            return ValidationResult(
                False, 
                "Серия паспорта не может начинаться с 0"
            )
        
        return ValidationResult(True, normalized=digits)
    
    # =========================================================================
    # Код подразделения
    # =========================================================================
    
    @staticmethod
    def validate_department_code(code: str) -> ValidationResult:
        """
        Валидация кода подразделения.
        
        Правила:
        - Ровно 6 цифр
        - Формат: XXX-XXX или XXXXXX
        
        Args:
            code: Строка с кодом подразделения
            
        Returns:
            ValidationResult с результатом и нормализованным значением (только цифры)
        """
        if not code or not code.strip():
            return ValidationResult(False, "Код подразделения не может быть пустым")
        
        # Оставляем только цифры
        digits = re.sub(r'\D', '', code)
        
        if len(digits) != 6:
            return ValidationResult(
                False, 
                f"Код подразделения должен содержать 6 цифр. Введено: {len(digits)} цифр"
            )
        
        return ValidationResult(True, normalized=digits)
    
    # =========================================================================
    # Номер телефона
    # =========================================================================
    
    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """
        Валидация номера телефона.
        
        Правила:
        - От 10 до 15 цифр
        - Поддерживаются форматы: +7..., 8..., 7...
        - Нормализуется к формату без кода страны (10 цифр)
        
        Args:
            phone: Строка с номером телефона
            
        Returns:
            ValidationResult с результатом и нормализованным значением
        """
        if not phone or not phone.strip():
            return ValidationResult(False, "Номер телефона не может быть пустым")
        
        # Оставляем только цифры
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) < 10:
            return ValidationResult(
                False, 
                f"Номер телефона слишком короткий. Минимум 10 цифр"
            )
        
        if len(digits) > 15:
            return ValidationResult(
                False, 
                f"Номер телефона слишком длинный. Максимум 15 цифр"
            )
        
        # Нормализация российских номеров
        if len(digits) == 11:
            # Формат 8XXXXXXXXXX или 7XXXXXXXXXX → XXXXXXXXXX
            if digits[0] in ('7', '8'):
                digits = digits[1:]
        elif len(digits) == 12:
            # Формат +7XXXXXXXXXX (если + был удален ранее)
            if digits[:2] == '79' or digits[:2] == '78':
                digits = digits[1:]
        
        return ValidationResult(True, normalized=digits)
    
    # =========================================================================
    # Причина добавления в ЧС
    # =========================================================================
    
    @staticmethod
    def validate_reason(reason: str, min_length: int = 3, max_length: int = 1000) -> ValidationResult:
        """
        Валидация причины добавления в черный список.
        
        Args:
            reason: Текст причины
            min_length: Минимальная длина (по умолчанию 3)
            max_length: Максимальная длина (по умолчанию 1000)
            
        Returns:
            ValidationResult с результатом
        """
        if not reason or not reason.strip():
            return ValidationResult(False, "Причина не может быть пустой")
        
        reason = reason.strip()
        
        if len(reason) < min_length:
            return ValidationResult(
                False, 
                f"Причина должна содержать минимум {min_length} символа"
            )
        
        if len(reason) > max_length:
            return ValidationResult(
                False, 
                f"Причина не должна превышать {max_length} символов"
            )
        
        return ValidationResult(True, normalized=reason)

