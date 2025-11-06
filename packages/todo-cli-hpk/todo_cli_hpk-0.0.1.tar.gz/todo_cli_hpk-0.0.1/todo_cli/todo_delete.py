from todo_cli.all_todos import is_sqlite_file
from todo_cli.main_cfg import Main_CFG
import logging
import click
from todo_cli.todo_add import db_connection


main_cfg = Main_CFG()


def remove_todo(todo_name: str, todo_id: str) -> bool:

    TODO_DB = main_cfg.TODO / f"{todo_name}.db"

    conn = None

    try:

        if not TODO_DB.exists():
            click.secho(f"{todo_name} not exists", fg="yellow")

            return False

        if not is_sqlite_file(TODO_DB):
            click.secho(f"{todo_name} is not a todo list", fg="yellow")

            return False

        conn = db_connection(TODO_DB)

        if not conn:

            return False

        cursor = conn.cursor()

        if not todo_id:

            click.secho(f"enter valid id from {todo_name}", fg="yellow")

            return False
        try:
            todo_id = int(todo_id)

        except (TypeError, ValueError):
            click.secho("Task id must be an integer.", fg="red")

            return False

        is_valid_id = cursor.execute("SELECT id FROM tasks where id=?", (todo_id,))
        if is_valid_id.fetchone() is None:

            click.secho("enter a valid id, no task found", fg="yellow")

            return False

        delete_query = f"""DELETE FROM tasks WHERE id=?"""
        cursor.execute(delete_query, (todo_id,))

        conn.commit()

        click.secho(f"task {todo_id} deleted successfully", fg="green")
        logging.info(f"task {todo_id} deleted successfully")

        return True

    except Exception as e:

        click.secho(f"{e}", fg="red")
        logging.error(f"{e}")
        return False

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":

    remove_todo()
