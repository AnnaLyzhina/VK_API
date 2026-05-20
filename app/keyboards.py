"""Клавиатуры для сообщений VK."""

import json


def get_main_keyboard():
    """Возвращает основную клавиатуру бота."""
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "Следующий"},
                    "color": "primary",
                },
                {
                    "action": {"type": "text", "label": "В избранное"},
                    "color": "positive",
                },
            ],
            [
                {
                    "action": {"type": "text", "label": "Избранное"},
                    "color": "secondary",
                },
                {
                    "action": {"type": "text", "label": "В чёрный список"},
                    "color": "negative",
                },
            ],
            [
                {
                    "action": {"type": "text", "label": "Новый поиск"},
                    "color": "secondary",
                },
                {
                    "action": {"type": "text", "label": "Помощь"},
                    "color": "secondary",
                },
            ],
        ],
    }
    return json.dumps(keyboard, ensure_ascii=False)