"""Точка входа в проект Vk."""

from app.bot import VkBot
from config import check_required_settings


if __name__ == "__main__":
    check_required_settings()
    bot = VkBot()
    bot.run()