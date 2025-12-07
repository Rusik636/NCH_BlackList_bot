"""Обработчики команд и сообщений бота."""

from src.bot.application.handlers.start import start_handler
from src.bot.application.handlers.id import id_handler

__all__ = ["start_handler", "id_handler"]

