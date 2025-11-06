from pathlib import Path as p
from todo_cli.all_todos import is_sqlite_file
from todo_cli.todo_add import db_connection
import click


def color_status(status):
    colors = {"pending": "yellow", "done": "green", "ongoing": "cyan"}
    return click.style(status, fg=colors.get(status, "white"))


def get_todo(path: str, todo_id: int | None = None) -> bool:
    TODO_DB = p.home() / ".todo" / f"{path}.db"
    conn = None
    try:
        if not TODO_DB.exists():
            click.secho(f"{path} not exists", fg="yellow")
            return False

        if not is_sqlite_file(TODO_DB):
            click.secho(f"{path} is not a todo list", fg="yellow")
            return False

        conn = db_connection(str(TODO_DB))
        if not conn:
            return False

        cursor = conn.cursor()

        if todo_id is not None:
            try:
                todo_id = int(todo_id)
            except (TypeError, ValueError):
                click.secho("Task id must be an integer.", fg="red")
                return False

        if todo_id is None:
            cursor.execute("SELECT * FROM tasks ORDER BY status, id;")
            todos = cursor.fetchall()

            if not todos:
                click.secho("No Task found.", fg="yellow")
                return True

            click.secho(f"{'ID':<4} {'Title':<20} {'Status':<12} {'Updated'}")
            click.secho("-" * 60)

            for t in todos:
                id, title, desc, status, created, updated = t
                updated_str = updated or created or ""
                click.echo(
                    f"{str(id):<4} {title:<20} {color_status(status):<12} {updated_str}"
                )
            return True

        else:
            cursor.execute("SELECT * FROM tasks WHERE id = (?);", (todo_id,))
            todo = cursor.fetchone()

            if not todo:
                click.secho("Todo not found.", fg="red")
                return False

            id, title, desc, status, created, updated = todo
            desc_str = desc or ""

            click.secho(
                f"{'ID':<4} {'Title':<20} {'Description':<35} {'Status':<12} {'Updated'}"
            )
            click.secho("-" * 100)

            click.echo(
                f"{str(id):<4} {title:<20} {desc_str:<35} {color_status(status):<12} {updated}"
            )
            return True

    except Exception as e:
        click.secho(f"{e}", fg="red")
        return False

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    get_todo()
