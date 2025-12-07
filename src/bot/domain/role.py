"""
Доменные сущности для системы ролей.
Определяет роли и их иерархию.
"""
from enum import Enum
from typing import List, Dict

# Приоритеты ролей (чем выше число, тем выше приоритет)
# Вынесено за пределы класса для корректной работы с Enum
_ROLE_PRIORITIES: Dict[str, int] = {
    "super_admin": 3,
    "admin": 2,
    "manager": 1,
}


class Role(str, Enum):
    """
    Роли пользователей в системе.
    
    Иерархия ролей (от высшей к низшей):
    - SUPER_ADMIN: Супер администратор (высший уровень доступа)
    - ADMIN: Администратор (средний уровень доступа)
    - MANAGER: Менеджер (базовый уровень доступа)
    
    Высшие роли автоматически имеют права низших ролей.
    """
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    
    @classmethod
    def get_priority(cls, role: "Role") -> int:
        """
        Получить приоритет роли.
        
        Args:
            role: Роль для получения приоритета
            
        Returns:
            Приоритет роли (число)
        """
        return _ROLE_PRIORITIES.get(role.value, 0)
    
    @classmethod
    def has_access(cls, user_role: "Role", required_role: "Role") -> bool:
        """
        Проверить, имеет ли пользователь с ролью user_role доступ к команде,
        требующей роль required_role.
        
        Логика: пользователь имеет доступ, если его приоритет >= приоритету требуемой роли.
        Это означает, что высшие роли имеют права низших ролей.
        
        Args:
            user_role: Роль пользователя
            required_role: Требуемая роль для доступа
            
        Returns:
            True, если пользователь имеет доступ, False иначе
        """
        user_priority = cls.get_priority(user_role)
        required_priority = cls.get_priority(required_role)
        return user_priority >= required_priority
    
    @classmethod
    def from_string(cls, role_str: str) -> "Role":
        """
        Преобразовать строку в роль.
        
        Args:
            role_str: Строковое представление роли
            
        Returns:
            Объект Role
            
        Raises:
            ValueError: Если роль не найдена
        """
        role_str = role_str.lower().strip()
        for role in cls:
            if role.value == role_str:
                return role
        raise ValueError(f"Неизвестная роль: {role_str}")
    
    @classmethod
    def get_all_roles(cls) -> List["Role"]:
        """
        Получить список всех ролей, отсортированных по приоритету (от высшей к низшей).
        
        Returns:
            Список ролей
        """
        return sorted(cls, key=lambda r: cls.get_priority(r), reverse=True)

