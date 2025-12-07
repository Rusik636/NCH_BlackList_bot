# Telegram Bot для управления арендой

Telegram бот на базе async telebot для управления арендой.

## Структура проекта

```
back_lict_rent/
├── main.py                 # Точка входа в приложение
├── src/
│   ├── config.py          # Конфигурация приложения (загрузка из .env)
│   ├── db/                # Модуль работы с базой данных
│   │   ├── connection.py  # Менеджер подключений к БД
│   │   └── table.py       # Определения таблиц
│   └── bot/               # Модуль Telegram бота
│       ├── application/   # Слой приложения (handlers)
│       ├── domain/        # Доменный слой (entities)
│       ├── repo/          # Слой репозиториев (data access)
│       └── service/       # Слой сервисов (business logic)
├── requirements.txt       # Зависимости проекта
└── .env                   # Переменные окружения (создать на основе .env.example)
```

## Установка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=lict_rent

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO
```

**Важно:** 
- Получите токен бота у [@BotFather](https://t.me/BotFather) в Telegram
- Замените `ADMIN_IDS` на реальные ID администраторов (через запятую)
- Настройте параметры подключения к базе данных PostgreSQL

### 3. Запуск бота

```bash
python main.py
```

## Архитектура

Проект следует принципам Clean Architecture с разделением на слои:

- **Application Layer** (`src/bot/application/`): Обработчики команд и сообщений
- **Domain Layer** (`src/bot/domain/`): Доменные сущности и бизнес-логика
- **Repository Layer** (`src/bot/repo/`): Абстракция доступа к данным
- **Service Layer** (`src/bot/service/`): Сервисы прикладного уровня

## Основные компоненты

### Config (`src/config.py`)

Загружает конфигурацию из переменных окружения:
- `BotConfig`: Конфигурация Telegram бота (токен, ID администраторов)
- `DatabaseConfig`: Конфигурация базы данных
- `Config`: Основная конфигурация приложения
- `setup_logging()`: Настройка логирования (вызывается автоматически при загрузке конфигурации)

Уровень логирования настраивается через переменную окружения `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR, CRITICAL). По умолчанию: INFO.

### DatabaseManager (`src/db/connection.py`)

Менеджер подключений к PostgreSQL:
- Пул подключений (asyncpg)
- Методы для выполнения запросов
- Управление жизненным циклом соединений

### BotApplication (`main.py`)

Основной класс приложения:
- Инициализация бота и БД
- Регистрация обработчиков
- Управление жизненным циклом приложения

## Безопасность

- Секреты хранятся в переменных окружения (не в коде)
- Использование parameterized queries через asyncpg
- Валидация входных данных
- Логирование без чувствительных данных

## Разработка

### Добавление новых команд

1. Создайте обработчик в `src/bot/application/handlers.py`
2. Зарегистрируйте его в функции `register_handlers()`

Пример:

```python
async def my_command_handler(message: Message, bot: AsyncTeleBot) -> None:
    await bot.reply_to(message, "Ответ на команду")

# В register_handlers():
bot.register_message_handler(
    my_command_handler,
    commands=["mycommand"],
    pass_bot=True,
)
```

## Зависимости

- `pyTelegramBotAPI==5.0.0` - Асинхронный клиент для Telegram Bot API
- `asyncpg==0.29.0` - Асинхронный драйвер PostgreSQL
- `python-dotenv==1.0.0` - Загрузка переменных окружения из .env

