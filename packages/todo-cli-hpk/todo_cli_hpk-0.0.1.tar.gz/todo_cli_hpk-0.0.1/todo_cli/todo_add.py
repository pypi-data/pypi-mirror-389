from pathlib import Path as p
from todo_cli.all_todos import is_sqlite_file
import sqlite3
import logging
import click


def db_connection(db_name: p):
    try:
        conn = sqlite3.connect(db_name)
        logging.info(f"successfully connect to {db_name}")
        return conn

    except Exception as e:
        logging.exception(f"could not connect to {db_name} : {e}")
        return None


def add_todo(todo: str, name: str, desc: str | None = None) -> bool:
    TODO_DB = p.home() / ".todo" / f"{todo}.db"
    conn = None
    try:
        if not TODO_DB.exists():
            click.secho(f"{todo} not exists", fg="yellow")
            return False

        if not is_sqlite_file(TODO_DB):
            click.secho(f"{todo} is not a todo list", fg="yellow")
            return False

        conn = db_connection(TODO_DB)

        if not conn:

            return False

        add_query = f"""
        INSERT INTO tasks (name,description) VALUES (?,?)

        """
        conn.execute(add_query, (name, desc))
        click.secho(f"a todo add to list: {todo}", fg="green")
        logging.info(f"a todo add to list: {todo}")
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        click.secho(f"A task named '{name}' already exists in '{todo}'!", fg="red")

        return False

    except Exception as e:
        click.secho(f"{e} \tunsuccessful add ", fg="yellow")
        logging.info(f"{e} \tunsuccessful add ")
        return False

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    add_todo()
