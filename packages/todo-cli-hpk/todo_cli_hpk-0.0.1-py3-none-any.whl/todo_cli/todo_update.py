from todo_cli.todo_add import db_connection
from todo_cli.all_todos import is_sqlite_file
import logging
import click
from datetime import datetime
from todo_cli.main_cfg import Main_CFG
from todo_cli.create import Status

main_cfg = Main_CFG()


def update_todo(
    todo_name: str,
    todo_id: str,
    todo_status: str | None = None,
    todo_desc: str | None = None,
) -> bool:

    TODO_DB = main_cfg.TODO / f"{todo_name}.db"

    conn = None
    try:
        if not TODO_DB.exists():
            click.secho(f"{todo_name} not exists", fg="yellow")

            return False

        if not is_sqlite_file(TODO_DB):
            click.secho(f"{todo_name} is not a todo list", fg="yellow")

            return False

        conn = db_connection(f"{TODO_DB}")

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

        if todo_status is not None:
            valid_status = [s.value for s in Status]
            if todo_status not in valid_status:
                click.secho(
                    f"Invalid status, choose one of { ' ,'.join(valid_status)}",
                    fg="red",
                )

                return False

        params = []
        values = []

        if todo_status is not None:
            params.append("status = ?")
            values.append(todo_status)
        if todo_desc is not None:
            params.append("description = ?")
            values.append(todo_desc)
        if not params:
            click.secho(
                "Nothing to update (no --status or --desc provided).", fg="yellow"
            )

            return False

        params.append("update_at = ?")
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values.append(update_time)
        values.append(todo_id)

        id_check = cursor.execute("SELECT id FROM tasks WHERE id = ?;", (todo_id,))
        if id_check.fetchone() is None:
            click.secho("Task not found.", fg="yellow")

            return False

        update_query = f"""
            UPDATE tasks SET {" ,".join(params)} WHERE id=?;
        """
        cursor.execute(update_query, values)
        conn.commit()

        click.secho(f"task {todo_id} updated successfully at {update_time}", fg="green")
        logging.info(f"task {todo_id} updated successfully")

        return True

    except Exception as e:
        click.secho(f"{e}", fg="red")
        logging.error(f"{e}")
        return False

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":

    update_todo()
