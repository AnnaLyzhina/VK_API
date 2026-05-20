"""Клиент для работы с VK API."""

import random

import vk_api
from vk_api.exceptions import ApiError
from vk_api.longpoll import VkEventType, VkLongPoll

from app.keyboards import get_main_keyboard
from config import TOKEN, USER_TOKEN


class VkClient:
    """Методы для общения с ВКонтакте."""

    def __init__(self):
        self.group_session = vk_api.VkApi(token=TOKEN)
        self.user_session = vk_api.VkApi(token=USER_TOKEN)
        self.group_api = self.group_session.get_api()
        self.user_api = self.user_session.get_api()
        self.longpoll = VkLongPoll(self.group_session)

    def listen(self):
        """Слушает новые сообщения сообщества."""
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                yield event

    def send_message(self, user_id, message, attachments=None):
        """Отправляет сообщение пользователю."""
        params = {
            "user_id": user_id,
            "message": message,
            "random_id": random.randint(1, 2_000_000_000),
            "keyboard": get_main_keyboard(),
        }

        if attachments:
            params["attachment"] = ",".join(attachments)

        self.group_api.messages.send(**params)

    def get_user_info(self, user_id):
        """Получает информацию о пользователе бота."""
        users = self.user_api.users.get(
            user_ids=user_id,
            fields="city,sex,bdate",
        )
        return users[0] if users else {}

    def search_candidates(self, age_from, age_to, sex, city_id, offset=0):
        """Ищет кандидатов через users.search."""
        try:
            result = self.user_api.users.search(
                count=20,
                offset=offset,
                age_from=age_from,
                age_to=age_to,
                sex=sex,
                city=city_id,
                status=6,
                has_photo=1,
                fields="city,sex,bdate,is_closed,can_access_closed",
            )
        except ApiError as error:
            print("Ошибка VK API при поиске:", error)
            return []

        items = result.get("items", [])
        return [item for item in items if self._is_open_profile(item)]

    def get_top_photos(self, owner_id):
        """Возвращает 3 популярные фотографии профиля."""
        try:
            result = self.user_api.photos.get(
                owner_id=owner_id,
                album_id="profile",
                extended=1,
                count=1000,
            )
        except ApiError as error:
            print("Ошибка VK API при получении фото:", error)
            return []

        photos = []
        for photo in result.get("items", []):
            likes_count = photo.get("likes", {}).get("count", 0)
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            photos.append(
                {
                    "id": photo["id"],
                    "owner_id": photo["owner_id"],
                    "likes_count": likes_count,
                    "attachment": attachment,
                }
            )

        photos.sort(key=lambda item: item["likes_count"], reverse=True)
        return photos[:3]

    @staticmethod
    def _is_open_profile(user):
        """Проверяет доступность профиля."""
        is_closed = user.get("is_closed", False)
        can_access = user.get("can_access_closed", True)
        return not is_closed or can_access
