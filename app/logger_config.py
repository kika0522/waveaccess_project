import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import settings


def setup_logging():
    """Настройка логирования с единым форматом даты"""
    import logging
    from logging.handlers import RotatingFileHandler

    # Удаляем все обработчики у корневого логгера
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Создаем логгер приложения
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)

    # Формат с локальным временем и миллисекундами
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S,%f"  # Пример: 2025-03-27 13:06:51,629
    )

    # Консольный обработчик (только если его нет)
    if not app_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

    # Отключаем передачу родительским логгерам
    app_logger.propagate = False

    return app_logger


# Инициализация при импорте
app_logger = setup_logging()