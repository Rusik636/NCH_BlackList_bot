"""
Сервис для проверки прав доступа пользователей.
"""
import logging
from typing import Optional

from src.bot.repo.admin_repository import AdminRepository
from src.bot.domain.role import Role

logger = logging.getLogger(__name__)


class AccessDeniedError(Exception):
    """Исключение при отказе в доступе."""
    pass


class AccessService:
    """Сервис для проверки прав доступа."""
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Инициализация сервиса доступа.
        
        Args:
            admin_repository: Репозиторий для работы с администраторами
        """
        self.admin_repository = admin_repository
    
    async def check_access(self, admin_id: int, required_role: Role) -> bool:
        """
        Проверить, имеет ли пользователь доступ к команде с требуемой ролью.
        
        Args:
            admin_id: Telegram ID пользователя
            required_role: Требуемая роль для доступа
            
        Returns:
            True, если пользователь имеет доступ, False иначе
            
        Raises:
            AccessDeniedError: Если пользователь не найден в базе или не имеет доступа
        """
        try:
            # Получаем информацию об администраторе
            admin = await self.admin_repository.get_by_admin_id(admin_id)
            
            if not admin:
                logger.warning(f"Пользователь {admin_id} не найден в базе администраторов")
                raise AccessDeniedError(f"Пользователь {admin_id} не является администратором")
            
            # Проверяем права доступа
            has_access = Role.has_access(admin.role, required_role)
            
            if not has_access:
                logger.warning(
                    f"Пользователь {admin_id} с ролью {admin.role.value} "
                    f"не имеет доступа к команде, требующей роль {required_role.value}"
                )
                raise AccessDeniedError(
                    f"Недостаточно прав. Требуется роль: {required_role.value}, "
                    f"ваша роль: {admin.role.value}"
                )
            
            logger.debug(
                f"Пользователь {admin_id} с ролью {admin.role.value} "
                f"имеет доступ к команде, требующей роль {required_role.value}"
            )
            return True
            
        except AccessDeniedError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа для пользователя {admin_id}: {e}", exc_info=True)
            raise AccessDeniedError("Ошибка при проверке прав доступа")

