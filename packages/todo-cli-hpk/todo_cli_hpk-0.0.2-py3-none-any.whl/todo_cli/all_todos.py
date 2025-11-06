from pathlib import Path as p
import re


def is_sqlite_file(path: p) -> bool:
    try:
        with path.open("rb") as f:
            header = f.read(15)
            return header.startswith(b"SQLite format 3")
    except Exception:
        return False


def all_todos() -> list:

    BASE_DIR = p.home() / ".todo"
    pattern = re.compile(r"^\w+\.db$", re.IGNORECASE)
    todos_list = []
    if BASE_DIR.exists():
        for db in BASE_DIR.iterdir():

            if (
                db.is_file()
                and re.match(pattern=pattern, string=str(db.name))
                and is_sqlite_file(db)
            ):
                todos_list.append(db)
        sorted_todo = sorted(todos_list, key=lambda x: x.stat().st_ctime, reverse=True)
        sorted_todo = [i.stem for i in sorted_todo]

    return sorted_todo


if __name__ == "__main__":
    all_todos()
