"""Основная логика VK-бота."""

from datetime import date

from app.repository import Repository
from app.vk_client import VkClient


class VkBot:
    """Бот для поиска анкет VK."""

    def __init__(self):
        self.vk = VkClient()
        self.repository = Repository()

        self.candidates = {}
        self.candidate_position = {}
        self.current_candidate = {}

    def run(self):
        """Запустить бота."""
        print("Bot started...")

        for event in self.vk.listen():
            text = event.text.strip()
            self.handle_message(event.user_id, text)

    def handle_message(self, user_id, text):
        """Обработать сообщение пользователя."""
        command = text.lower()
        bot_user_id = self._get_bot_user_id(user_id)

        if command in {"привет", "начать", "старт", "новый поиск"}:
            self._start_search(user_id, bot_user_id)
        elif command == "следующий":
            self._show_next_candidate(user_id, bot_user_id)
        elif command == "в избранное":
            self._add_to_favorites(user_id, bot_user_id)
        elif command in {"в черный список", "в чёрный список"}:
            self._add_to_blacklist(user_id, bot_user_id)
        elif command == "избранное":
            self._show_favorites(user_id, bot_user_id)
        elif command == "помощь":
            self._send_help(user_id)
        else:
            self.vk.send_message(
                user_id,
                "Я не понял команду. Напишите 'Привет' для начала поиска.",
            )

    def _get_bot_user_id(self, user_id):
        """Создать или получить пользователя бота из БД."""
        user_info = self.vk.get_user_info(user_id)

        return self.repository.get_or_create_bot_user(
            user_id,
            user_info.get("first_name", ""),
            user_info.get("last_name", ""),
        )

    def _start_search(self, user_id, bot_user_id):
        """Начать новый поиск кандидатов."""
        user_info = self.vk.get_user_info(user_id)
        settings = self._make_search_settings(user_info)

        if settings is None:
            self.vk.send_message(
                user_id,
                "Не удалось определить параметры поиска.\n"
                "Проверьте, что в профиле VK открыты город, пол "
                "и дата рождения с годом.",
            )
            return

        self.repository.update_search_settings(
            vk_user_id=user_id,
            age_from=settings["age_from"],
            age_to=settings["age_to"],
            sex=settings["sex"],
            city_id=settings["city_id"],
        )

        found_candidates = self.vk.search_candidates(
            age_from=settings["age_from"],
            age_to=settings["age_to"],
            sex=settings["sex"],
            city_id=settings["city_id"],
        )

        self.candidates[user_id] = found_candidates
        self.candidate_position[user_id] = 0
        self.current_candidate[user_id] = None

        self.vk.send_message(
            user_id,
            "Параметры поиска определены автоматически:\n"
            f"возраст от {settings['age_from']} до {settings['age_to']}, "
            f"город ID {settings['city_id']}.\n"
            "Ищу подходящего кандидата.",
        )

        self._show_next_candidate(user_id, bot_user_id)

    def _make_search_settings(self, user_info):
        """Сформировать параметры поиска из профиля пользователя."""
        user_age = self._get_age(user_info.get("bdate"))
        user_sex = user_info.get("sex")
        city = user_info.get("city") or {}
        city_id = city.get("id")

        if not user_age or not city_id or user_sex not in (1, 2):
            return None

        search_sex = 1 if user_sex == 2 else 2

        return {
            "age_from": max(user_age - 5, 18),
            "age_to": user_age + 5,
            "sex": search_sex,
            "city_id": city_id,
        }

    @staticmethod
    def _get_age(bdate):
        """Посчитать возраст по дате рождения из VK."""
        if not bdate:
            return None

        parts = bdate.split(".")

        if len(parts) != 3:
            return None

        day, month, year = parts

        if not day.isdigit() or not month.isdigit() or not year.isdigit():
            return None

        birthday = date(int(year), int(month), int(day))
        today = date.today()
        age = today.year - birthday.year

        if (today.month, today.day) < (birthday.month, birthday.day):
            age -= 1

        return age

    def _show_next_candidate(self, user_id, bot_user_id):
        """Показать следующего кандидата."""
        candidates = self.candidates.get(user_id, [])
        position = self.candidate_position.get(user_id, 0)

        while position < len(candidates):
            candidate = candidates[position]
            self.candidate_position[user_id] = position + 1
            position += 1

            if candidate["id"] == user_id:
                continue

            candidate_id = self.repository.save_candidate(candidate)

            if self.repository.is_blacklisted(bot_user_id, candidate_id):
                continue

            if self.repository.is_viewed(bot_user_id, candidate_id):
                continue

            photos = self.vk.get_top_photos(candidate["id"])

            self.repository.save_photos(candidate_id, photos)
            self.repository.add_to_viewed(bot_user_id, candidate_id)

            self.current_candidate[user_id] = {
                "candidate_id": candidate_id,
                "candidate": candidate,
                "photos": photos,
            }

            self._send_candidate(user_id, candidate, photos)
            return

        self.vk.send_message(
            user_id,
            "Кандидаты закончились. Напишите 'Новый поиск'.",
        )

    def _send_candidate(self, user_id, candidate, photos):
        """Отправить кандидата пользователю."""
        profile_url = f"https://vk.com/id{candidate['id']}"
        full_name = (
            f"{candidate.get('first_name', '')} "
            f"{candidate.get('last_name', '')}"
        )
        message = f"{full_name}\nПрофиль: {profile_url}"
        attachments = [photo["attachment"] for photo in photos]

        self.vk.send_message(user_id, message, attachments)

    def _add_to_favorites(self, user_id, bot_user_id):
        """Добавить текущего кандидата в избранное."""
        current = self.current_candidate.get(user_id)

        if current is None:
            self.vk.send_message(user_id, "Сначала нужно показать кандидата.")
            return

        candidate_id = current["candidate_id"]

        if self.repository.is_blacklisted(bot_user_id, candidate_id):
            self.vk.send_message(
                user_id,
                "Этот кандидат уже в чёрном списке.",
            )
            return

        if self.repository.is_favorite(bot_user_id, candidate_id):
            self.vk.send_message(
                user_id,
                "Этот кандидат уже есть в избранном.",
            )
            return

        self.repository.add_to_favorites(bot_user_id, candidate_id)
        self.vk.send_message(user_id, "Кандидат добавлен в избранное.")

    def _add_to_blacklist(self, user_id, bot_user_id):
        """Добавить текущего кандидата в чёрный список."""
        current = self.current_candidate.get(user_id)

        if current is None:
            self.vk.send_message(user_id, "Сначала нужно показать кандидата.")
            return

        candidate_id = current["candidate_id"]

        if self.repository.is_blacklisted(bot_user_id, candidate_id):
            self.vk.send_message(
                user_id,
                "Этот кандидат уже есть в чёрном списке.",
            )
            self._show_next_candidate(user_id, bot_user_id)
            return

        if self.repository.is_favorite(bot_user_id, candidate_id):
            self.repository.remove_from_favorites(bot_user_id, candidate_id)
            self.vk.send_message(
                user_id,
                "Кандидат был в избранном. "
                "Я удалил его из избранного.",
            )

        self.repository.add_to_blacklist(bot_user_id, candidate_id)
        self.vk.send_message(user_id, "Кандидат добавлен в чёрный список.")
        self._show_next_candidate(user_id, bot_user_id)

    def _show_favorites(self, user_id, bot_user_id):
        """Показать список избранных кандидатов."""
        favorites = self.repository.get_favorites(bot_user_id)

        if not favorites:
            self.vk.send_message(user_id, "Список избранных пока пуст.")
            return

        text = "Ваш список избранных:\n"

        for item in favorites:
            text += (
                f"{item['first_name']} {item['last_name']} — "
                f"{item['profile_url']}\n"
            )

        self.vk.send_message(user_id, text)

    def _send_help(self, user_id):
        """Отправить список команд."""
        self.vk.send_message(
            user_id,
            "Команды:\n"
            "Привет — начать поиск\n"
            "Следующий — показать следующего кандидата\n"
            "В избранное — сохранить кандидата\n"
            "Избранное — показать сохранённых\n"
            "В чёрный список — больше не показывать кандидата\n"
            "Новый поиск — начать поиск заново",
        )
