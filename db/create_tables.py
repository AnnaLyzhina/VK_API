"""Создание таблиц в базе данных PostgreSQL.

Запускать один раз после создания базы данных vk:
python db/create_tables.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.database import execute_schema  # noqa: E402


if __name__ == "__main__":
    schema_path = PROJECT_ROOT / "db" / "schema.sql"
    execute_schema(schema_path)
    print("Таблицы успешно созданы или уже существовали.")