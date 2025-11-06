import sqlite3
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    PENDING = "pending"
    ONGOING = "ongoing"
    DONE = "done"


def create_db(name: str) -> str:
    todo_dir = Path.home() / ".todo"
    todo_dir.mkdir(mode=0o700, exist_ok=True)
    db_path = todo_dir / f"{name}.db"

    with sqlite3.connect(str(db_path)) as connection:
        cursor = connection.cursor()

        create_todo_table_query = """
        CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','ongoing','done')),
        create_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        update_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );"""

        cursor.execute(create_todo_table_query)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
        connection.commit()


if __name__ == "__main__":
    create_db()
