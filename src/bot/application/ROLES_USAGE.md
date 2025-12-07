# Система ролей и контроля доступа

## Описание

Система контроля доступа основана на иерархии ролей. Высшие роли автоматически имеют права низших ролей.

## Иерархия ролей

1. **SUPER_ADMIN** (Супер администратор) - высший уровень доступа
   - Имеет доступ ко всем командам
   - Приоритет: 3

2. **ADMIN** (Администратор) - средний уровень доступа
   - Имеет доступ к командам для администраторов и менеджеров
   - Приоритет: 2

3. **MANAGER** (Менеджер) - базовый уровень доступа
   - Имеет доступ только к командам для менеджеров
   - Приоритет: 1

## Логика работы

- **Высшие роли имеют права низших**: SUPER_ADMIN может выполнять команды для ADMIN и MANAGER
- **Низшие роли не имеют прав высших**: MANAGER не может выполнять команды для ADMIN или SUPER_ADMIN

## Использование декоратора

### Базовый пример

```python
from src.bot.application.decorators import require_role
from src.bot.domain.role import Role
from telebot.types import Message

async def my_command(message: Message) -> None:
    """Команда для менеджеров и выше."""
    await message.bot.reply_to(message, "Команда выполнена")

# В register_handlers:
bot.message_handler(commands=["my_command"])(
    require_role(Role.MANAGER, context.access_service)(my_command)
)
```

### Примеры для разных ролей

```python
# Команда для менеджеров (MANAGER, ADMIN, SUPER_ADMIN)
bot.message_handler(commands=["manager_cmd"])(
    require_role(Role.MANAGER, context.access_service)(manager_handler)
)

# Команда для администраторов (ADMIN, SUPER_ADMIN)
bot.message_handler(commands=["admin_cmd"])(
    require_role(Role.ADMIN, context.access_service)(admin_handler)
)

# Команда только для супер администраторов (SUPER_ADMIN)
bot.message_handler(commands=["super_admin_cmd"])(
    require_role(Role.SUPER_ADMIN, context.access_service)(super_admin_handler)
)
```

## Добавление администраторов в базу данных

Для того чтобы пользователь мог выполнять команды, его нужно добавить в таблицу `admins`:

```sql
INSERT INTO admins (admin_id, role) 
VALUES (123456789, 'super_admin');
```

Доступные значения роли:
- `super_admin`
- `admin`
- `manager`

## Обработка ошибок доступа

Если пользователь не имеет доступа к команде:
1. Выбрасывается исключение `AccessDeniedError`
2. Пользователю отправляется сообщение об отказе в доступе
3. В лог записывается информация о попытке доступа

## Структура компонентов

- **Domain Layer** (`src/bot/domain/`):
  - `role.py` - определение ролей и логика проверки доступа
  - `admin.py` - доменная сущность администратора

- **Repository Layer** (`src/bot/repo/`):
  - `admin_repository.py` - работа с администраторами в БД

- **Service Layer** (`src/bot/service/`):
  - `access_service.py` - проверка прав доступа

- **Application Layer** (`src/bot/application/`):
  - `decorators.py` - декоратор `require_role`
  - `context.py` - контекст приложения с зависимостями

