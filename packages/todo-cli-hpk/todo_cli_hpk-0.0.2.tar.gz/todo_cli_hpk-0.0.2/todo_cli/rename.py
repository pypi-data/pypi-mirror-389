from pathlib import Path as p
from .all_todos import is_sqlite_file
import logging
import click


def rename_todo_list(old_name: str, new_name: str) -> bool:

    base_dir = p.home() / ".todo"
    old_todo = base_dir / f"{old_name}.db"
    new_todo = base_dir / f"{new_name}.db"

    try:
        if not old_todo.exists():
            logging.warning(f"Rename failed: '{old_name}' not found.")
            click.secho(f"Rename failed: '{old_name}' not found.", fg="yellow")
            return False
        if not is_sqlite_file(old_todo):
            logging.warning(f"Rename failed: '{old_name}' is not a valid SQLite file.")
            click.secho(
                f"Rename failed: '{old_name}' is not a valid SQLite file.", fg="yellow"
            )
            return False

        if new_todo.exists():
            logging.warning(f"Rename failed: '{new_name}' already exists.")
            click.secho(f"Rename failed: '{new_name}' already exists.", fg="yellow")
            return False

        old_todo.rename(new_todo)
        logging.info(f"Renamed '{old_name}.db' to '{new_name}.db' successfully.")
        click.secho(
            f"'{old_name}' todo list renamed to '{new_name}' successfully.", fg="green"
        )

        return True

    except Exception as e:
        logging.exception(f"Error renaming '{old_name}.db': {e}")
        return False


if __name__ == "__main__":
    rename_todo_list()
