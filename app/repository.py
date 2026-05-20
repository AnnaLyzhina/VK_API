"""Работа с базой данных PostgreSQL без SQLAlchemy."""

from app.database import get_connection


class Repository:
    """Класс с SQL-запросами проекта."""

    def get_or_create_bot_user(self, vk_user_id, first_name="", last_name=""):
        """Создаёт или возвращает пользователя бота."""
        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO bot_users (vk_user_id, first_name, last_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (vk_user_id) DO UPDATE
                        SET first_name = EXCLUDED.first_name,
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
        """Сохраняет параметры поиска."""
        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE bot_users
                        SET age_from = %s,
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
        """Сохраняет кандидата и возвращает id в БД."""
        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO candidates
                            (vk_id, first_name, last_name, profile_url,
                             city_id, age, sex)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vk_id) DO UPDATE
                        SET first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            profile_url = EXCLUDED.profile_url
                        RETURNING id;
                        """,
                        (
                            candidate["id"],
                            candidate.get("first_name", ""),
                            candidate.get("last_name", ""),
                            f"https://vk.com/id{candidate['id']}",
                            candidate.get("city_id"),
                            candidate.get("age"),
                            candidate.get("sex"),
                        ),
                    )
                    return cursor.fetchone()["id"]
        finally:
            connection.close()

    def save_photos(self, candidate_id, photos):
        """Сохраняет фотографии кандидата."""
        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    for photo in photos:
                        cursor.execute(
                            """
                            INSERT INTO photos
                                (candidate_id, owner_id, photo_id,
                                 likes_count, attachment)
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
        """Добавляет кандидата в избранное."""
        self._insert_link("favorites", bot_user_id, candidate_id)

    def add_to_blacklist(self, bot_user_id, candidate_id):
        """Добавляет кандидата в чёрный список."""
        self._insert_link("blacklist", bot_user_id, candidate_id)

    def add_to_viewed(self, bot_user_id, candidate_id):
        """Помечает кандидата как просмотренного."""
        self._insert_link("viewed_candidates", bot_user_id, candidate_id)

    def _insert_link(self, table_name, bot_user_id, candidate_id):
        """Добавляет связь пользователя и кандидата."""
        allowed_tables = {"favorites", "blacklist", "viewed_candidates"}
        if table_name not in allowed_tables:
            raise ValueError("Недопустимое имя таблицы")

        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (bot_user_id, candidate_id)
                        VALUES (%s, %s)
                        ON CONFLICT (bot_user_id, candidate_id) DO NOTHING;
                        """,
                        (bot_user_id, candidate_id),
                    )
        finally:
            connection.close()

    def is_hidden_candidate(self, bot_user_id, candidate_id):
        """Проверяет, скрыт ли кандидат."""
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM blacklist
                        WHERE bot_user_id = %s AND candidate_id = %s
                    ) AS in_blacklist,
                    EXISTS(
                        SELECT 1 FROM viewed_candidates
                        WHERE bot_user_id = %s AND candidate_id = %s
                    ) AS in_viewed;
                    """,
                    (bot_user_id, candidate_id, bot_user_id, candidate_id),
                )
                row = cursor.fetchone()
                return row["in_blacklist"] or row["in_viewed"]
        finally:
            connection.close()

    def get_favorites(self, bot_user_id):
        """Возвращает список избранных кандидатов."""
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT c.first_name, c.last_name, c.profile_url
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