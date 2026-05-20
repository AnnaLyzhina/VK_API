"""Основная логика VK-бота."""

from app.repository import Repository
from app.vk_client import VkClient


class VkBot:
    """Бот для поиска людей во ВКонтакте."""

    def __init__(self):
        self.vk = VkClient()
        self.repository = Repository()
        self.states = {}
        self.search_results = {}
        self.current_candidate = {}

    def run(self):
        """Запускает бота."""
        print("Bot started...")
        for event in self.vk.listen():
            self.handle_message(event.user_id, event.text.strip())

    def handle_message(self, user_id, text):
        """Обрабатывает входящее сообщение."""
        text_lower = text.lower()
        bot_user_id = self._prepare_bot_user(user_id)

        if text_lower in {"привет", "начать", "старт", "новый поиск"}:
            self._start_search(user_id)
        elif user_id in self.states:
            self._process_search_state(user_id, text)
        elif text_lower == "следующий":
            self._show_next_candidate(user_id, bot_user_id)
        elif text_lower == "в избранное":
            self._add_current_to_favorites(user_id, bot_user_id)
        elif text_lower in {"в черный список", "в чёрный список"}:
            self._add_current_to_blacklist(user_id, bot_user_id)
        elif text_lower == "избранное":
            self._show_favorites(user_id, bot_user_id)
        elif text_lower == "помощь":
            self._send_help(user_id)
        else:
            self.vk.send_message(
                user_id,
                "Я не понял команду. Напишите 'Привет'.",
            )

    def _prepare_bot_user(self, user_id):
        """Создаёт пользователя бота в БД."""
        user_info = self.vk.get_user_info(user_id)
        return self.repository.get_or_create_bot_user(
            user_id,
            user_info.get("first_name", ""),
            user_info.get("last_name", ""),
        )

    def _start_search(self, user_id):
        """Начинает новый поиск."""
        self.states[user_id] = {"step": "age_from"}
        self.search_results[user_id] = []
        self.current_candidate[user_id] = None
        self.vk.send_message(user_id, "Введите минимальный возраст, например: 18")

    def _process_search_state(self, user_id, text):
        """Заполняет параметры поиска по шагам."""
        state = self.states[user_id]
        step = state["step"]

        if step == "age_from":
            if not text.isdigit():
                self.vk.send_message(user_id, "Возраст нужно ввести числом.")
                return
            state["age_from"] = int(text)
            state["step"] = "age_to"
            self.vk.send_message(
                user_id,
                "Введите максимальный возраст, например: 35",
            )

        elif step == "age_to":
            if not text.isdigit():
                self.vk.send_message(user_id, "Возраст нужно ввести числом.")
                return
            state["age_to"] = int(text)
            state["step"] = "sex"
            self.vk.send_message(user_id, "Введите пол: 1 — женщина, 2 — мужчина")

        elif step == "sex":
            if text not in {"1", "2"}:
                self.vk.send_message(user_id, "Введите только 1 или 2.")
                return
            state["sex"] = int(text)
            state["step"] = "city_id"
            self.vk.send_message(
                user_id,
                "Введите ID города VK. Москва — 1, Санкт-Петербург — 2.",
            )

        elif step == "city_id":
            if not text.isdigit():
                self.vk.send_message(user_id, "ID города нужно ввести числом.")
                return
            state["city_id"] = int(text)
            self._finish_search_settings(user_id, state)

    def _finish_search_settings(self, user_id, state):
        """Сохраняет параметры и запускает поиск."""
        self.repository.update_search_settings(
            vk_user_id=user_id,
            age_from=state["age_from"],
            age_to=state["age_to"],
            sex=state["sex"],
            city_id=state["city_id"],
        )
        del self.states[user_id]

        candidates = self.vk.search_candidates(
            age_from=state["age_from"],
            age_to=state["age_to"],
            sex=state["sex"],
            city_id=state["city_id"],
        )

        self.search_results[user_id] = candidates
        self.vk.send_message(
            user_id,
            "Поиск выполнен. Показываю первого кандидата.",
        )
        bot_user_id = self._prepare_bot_user(user_id)
        self._show_next_candidate(user_id, bot_user_id)

    def _show_next_candidate(self, user_id, bot_user_id):
        """Показывает следующего подходящего кандидата."""
        candidates = self.search_results.get(user_id, [])

        while candidates:
            candidate = candidates.pop(0)
            candidate_id = self.repository.save_candidate(candidate)

            if self.repository.is_hidden_candidate(bot_user_id, candidate_id):
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
            "Кандидаты закончились. Нажмите 'Новый поиск'.",
        )

    def _send_candidate(self, user_id, candidate, photos):
        """Отправляет карточку кандидата в чат."""
        profile_url = f"https://vk.com/id{candidate['id']}"
        message = (
            f"{candidate.get('first_name', '')} "
            f"{candidate.get('last_name', '')}\n"
            f"Профиль: {profile_url}"
        )
        attachments = [photo["attachment"] for photo in photos]
        self.vk.send_message(user_id, message, attachments)

    def _add_current_to_favorites(self, user_id, bot_user_id):
        """Добавляет текущего кандидата в избранное."""
        current = self.current_candidate.get(user_id)
        if not current:
            self.vk.send_message(user_id, "Сначала нужно показать кандидата.")
            return

        self.repository.add_to_favorites(bot_user_id, current["candidate_id"])
        self.vk.send_message(user_id, "Кандидат добавлен в избранное.")

    def _add_current_to_blacklist(self, user_id, bot_user_id):
        """Добавляет текущего кандидата в чёрный список."""
        current = self.current_candidate.get(user_id)
        if not current:
            self.vk.send_message(user_id, "Сначала нужно показать кандидата.")
            return

        self.repository.add_to_blacklist(bot_user_id, current["candidate_id"])
        self.vk.send_message(user_id, "Кандидат добавлен в чёрный список.")
        self._show_next_candidate(user_id, bot_user_id)

    def _show_favorites(self, user_id, bot_user_id):
        """Показывает список избранных кандидатов."""
        favorites = self.repository.get_favorites(bot_user_id)
        if not favorites:
            self.vk.send_message(user_id, "Список избранных пока пуст.")
            return

        lines = ["Ваш список избранных:"]
        for item in favorites:
            lines.append(
                f"{item['first_name']} {item['last_name']} — "
                f"{item['profile_url']}"
            )

        self.vk.send_message(user_id, "\n".join(lines))

    def _send_help(self, user_id):
        """Отправляет справку по командам."""
        self.vk.send_message(
            user_id,
            "Команды бота:\n"
            "Привет — начать поиск\n"
            "Следующий — показать следующего кандидата\n"
            "В избранное — сохранить кандидата\n"
            "Избранное — показать сохранённых\n"
            "В чёрный список — больше не показывать кандидата\n"
            "Новый поиск — задать новые параметры",
        )
