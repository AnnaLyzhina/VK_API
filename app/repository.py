"""Работа с базой данных PostgreSQL."""

from app.database import get_connection


class Repository:
    """SQL-запросы для работы бота."""

    def get_or_create_bot_user(self, vk_user_id, first_name="", last_name=""):
        """Создать пользователя бота или вернуть его id."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO bot_users
                            (vk_user_id, first_name, last_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (vk_user_id)
                        DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name
                        RETURNING id;
                        """,
                        (vk_user_id, first_name, last_name),
                    )
                    return cursor.fetchone()["id"]
        finally:
            connection.close()

    def update_search_settings(
        self,
        vk_user_id,
        age_from,
        age_to,
        sex,
        city_id,
    ):
        """Сохранить параметры поиска пользователя."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE bot_users
                        SET
                            age_from = %s,
                            age_to = %s,
                            sex = %s,
                            city_id = %s
                        WHERE vk_user_id = %s;
                        """,
                        (age_from, age_to, sex, city_id, vk_user_id),
                    )
        finally:
            connection.close()

    def save_candidate(self, candidate):
        """Сохранить кандидата и вернуть его id из базы."""
        city = candidate.get("city") or {}
        city_id = city.get("id") or candidate.get("city_id")

        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO candidates
                            (
                                vk_id,
                                first_name,
                                last_name,
                                profile_url,
                                city_id,
                                age,
                                sex
                            )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vk_id)
                        DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            profile_url = EXCLUDED.profile_url,
                            city_id = EXCLUDED.city_id,
                            age = EXCLUDED.age,
                            sex = EXCLUDED.sex
                        RETURNING id;
                        """,
                        (
                            candidate["id"],
                            candidate.get("first_name", ""),
                            candidate.get("last_name", ""),
                            f"https://vk.com/id{candidate['id']}",
                            city_id,
                            candidate.get("age"),
                            candidate.get("sex"),
                        ),
                    )
                    return cursor.fetchone()["id"]
        finally:
            connection.close()

    def save_photos(self, candidate_id, photos):
        """Сохранить фотографии кандидата."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    for photo in photos:
                        cursor.execute(
                            """
                            INSERT INTO photos
                                (
                                    candidate_id,
                                    owner_id,
                                    photo_id,
                                    likes_count,
                                    attachment
                                )
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (owner_id, photo_id) DO NOTHING;
                            """,
                            (
                                candidate_id,
                                photo["owner_id"],
                                photo["id"],
                                photo.get("likes_count", 0),
                                photo["attachment"],
                            ),
                        )
        finally:
            connection.close()

    def add_to_favorites(self, bot_user_id, candidate_id):
        """Добавить кандидата в избранное."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO favorites
                            (bot_user_id, candidate_id)
                        VALUES (%s, %s)
                        ON CONFLICT (bot_user_id, candidate_id) DO NOTHING
                        RETURNING id;
                        """,
                        (bot_user_id, candidate_id),
                    )
                    return cursor.fetchone() is not None
        finally:
            connection.close()

    def add_to_blacklist(self, bot_user_id, candidate_id):
        """Добавить кандидата в чёрный список."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO blacklist
                            (bot_user_id, candidate_id)
                        VALUES (%s, %s)
                        ON CONFLICT (bot_user_id, candidate_id) DO NOTHING
                        RETURNING id;
                        """,
                        (bot_user_id, candidate_id),
                    )
                    return cursor.fetchone() is not None
        finally:
            connection.close()

    def add_to_viewed(self, bot_user_id, candidate_id):
        """Добавить кандидата в просмотренные."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO viewed_candidates
                            (bot_user_id, candidate_id)
                        VALUES (%s, %s)
                        ON CONFLICT (bot_user_id, candidate_id) DO NOTHING;
                        """,
                        (bot_user_id, candidate_id),
                    )
        finally:
            connection.close()

    def is_favorite(self, bot_user_id, candidate_id):
        """Проверить, есть ли кандидат в избранном."""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM favorites
                    WHERE bot_user_id = %s
                      AND candidate_id = %s;
                    """,
                    (bot_user_id, candidate_id),
                )
                return cursor.fetchone() is not None
        finally:
            connection.close()

    def is_blacklisted(self, bot_user_id, candidate_id):
        """Проверить, есть ли кандидат в чёрном списке."""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM blacklist
                    WHERE bot_user_id = %s
                      AND candidate_id = %s;
                    """,
                    (bot_user_id, candidate_id),
                )
                return cursor.fetchone() is not None
        finally:
            connection.close()

    def is_viewed(self, bot_user_id, candidate_id):
        """Проверить, был ли кандидат уже просмотрен."""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM viewed_candidates
                    WHERE bot_user_id = %s
                      AND candidate_id = %s;
                    """,
                    (bot_user_id, candidate_id),
                )
                return cursor.fetchone() is not None
        finally:
            connection.close()

    def remove_from_favorites(self, bot_user_id, candidate_id):
        """Удалить кандидата из избранного."""
        connection = get_connection()

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM favorites
                        WHERE bot_user_id = %s
                          AND candidate_id = %s;
                        """,
                        (bot_user_id, candidate_id),
                    )
        finally:
            connection.close()

    def get_favorites(self, bot_user_id):
        """Получить список избранных кандидатов."""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        c.first_name,
                        c.last_name,
                        c.profile_url
                    FROM favorites f
                    JOIN candidates c ON c.id = f.candidate_id
                    WHERE f.bot_user_id = %s
                    ORDER BY f.created_at DESC;
                    """,
                    (bot_user_id,),
                )
                return cursor.fetchall()
        finally:
            connection.close()
