"""Настройки проекта.

Все секретные данные берутся из файла .env.
Файл .env нельзя загружать на GitHub.
"""

from os import getenv

from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN", "")
USER_TOKEN = getenv("USER_TOKEN", "")
GROUP_ID = getenv("GROUP_ID", "")
VK_API_VERSION = getenv("VK_API_VERSION", "5.199")

DB_NAME = getenv("DB_NAME", "vk")
DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "")
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "5432")


def check_required_settings():
    """Проверяет, что важные настройки заполнены."""
    required_values = {
        "TOKEN": TOKEN,
        "USER_TOKEN": USER_TOKEN,
        "DB_PASSWORD": DB_PASSWORD,
    }

    empty_values = [name for name, value in required_values.items() if not value]

    if empty_values:
        missed = ", ".join(empty_values)
        raise ValueError(
            "Не заполнены обязательные значения в .env: "
            f"{missed}. Проверьте файл .env."
        )
