"""
Декораторы для обработчиков бота.
"""
import logging
import functools
from typing import Callable, Any

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.bot.domain.role import Role
from src.bot.service.access_service import AccessService, AccessDeniedError

logger = logging.getLogger(__name__)


def require_role(required_role: Role, access_service: AccessService):
    """
    Декоратор для проверки прав доступа к команде.
    
    Перед выполнением функции проверяет, имеет ли пользователь требуемую роль.
    Высшие роли автоматически имеют права низших ролей.
    
    Args:
        required_role: Требуемая роль для доступа к команде
        access_service: Сервис для проверки прав доступа
        
    Returns:
        Декорированная функция
        
    Example:
        @require_role(Role.ADMIN, access_service)
        async def admin_command(message: Message, bot: AsyncTeleBot):
            await bot.reply_to(message, "Команда для админов")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(message: Message, bot: AsyncTeleBot, *args: Any, **kwargs: Any) -> Any:
            try:
                admin_id = message.from_user.id
                
                # Проверяем права доступа
                await access_service.check_access(admin_id, required_role)
                
                # Если доступ разрешен, выполняем функцию
                return await func(message, bot, *args, **kwargs)
                
            except AccessDeniedError as e:
                # Отправляем сообщение об отказе в доступе
                error_message = f"❌ Доступ запрещен.\n\n{str(e)}"
                await bot.reply_to(message, error_message)
                logger.info(
                    f"Пользователь {message.from_user.id} (@{message.from_user.username}) "
                    f"получил отказ в доступе к команде, требующей роль {required_role.value}"
                )
                return None
            except Exception as e:
                logger.error(
                    f"Ошибка при выполнении команды для пользователя {message.from_user.id}: {e}",
                    exc_info=True
                )
                await bot.reply_to(
                    message,
                    "❌ Произошла ошибка при выполнении команды. Попробуйте позже."
                )
                return None
        
        return wrapper
    return decorator

