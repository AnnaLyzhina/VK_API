"""Подключение к PostgreSQL без SQLAlchemy."""

from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def get_connection():
    """Создаёт подключение к базе данных."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        cursor_factory=RealDictCursor,
    )


def execute_schema(schema_path: Path):
    """Выполняет SQL-файл со схемой базы данных."""
    sql = schema_path.read_text(encoding="utf-8")

    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
    finally:
        connection.close()
