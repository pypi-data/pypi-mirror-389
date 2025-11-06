from pathlib import Path as p
from .all_todos import is_sqlite_file
import logging


def delete_todo(name: str) -> bool:

    TODO_FILE = p.home() / ".todo" / f"{name}.db"

    try:
        if TODO_FILE.exists() and TODO_FILE.is_file() and is_sqlite_file(TODO_FILE):
            TODO_FILE.unlink()
            return True
        else:
            return False
    except Exception as e:
        logging.exception(f"Error deleting {TODO_FILE}: {e}")
        return False


if __name__ == "__main__":
    delete_todo("firstt")
