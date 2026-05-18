from pathlib import Path

from analyzers.file_types import count_file_types
from analyzers.todos import find_todos, find_todos_in_text
from models import ScannedFile


def test_find_todos_in_text_parses_without_file_io():
    todos = find_todos_in_text(
        path=Path("app.py"),
        relative_path=Path("app.py"),
        text="# TODO: add cli\nprint('TODO: not a comment')\n",
        keywords=("TODO", "FIXME"),
    )

    assert len(todos) == 1
    assert todos[0].relative_path == Path("app.py")
    assert todos[0].line_number == 1
    assert todos[0].keyword == "TODO"


def test_find_todos_returns_empty_when_keywords_are_empty(tmp_path: Path):
    path = tmp_path / "app.py"
    path.write_text("# TODO: add cli\n", encoding="utf-8")
    files = [
        ScannedFile(
            path=path,
            relative_path=Path("app.py"),
            suffix=".py",
            size=path.stat().st_size,
        )
    ]

    assert find_todos(files, keywords=()) == []


def test_count_file_types_accepts_iterables():
    files = (
        ScannedFile(
            path=Path(name),
            relative_path=Path(name),
            suffix=suffix,
            size=0,
        )
        for name, suffix in (("app.py", ".py"), ("README", ""))
    )

    assert count_file_types(files) == {".py": 1, "[no extension]": 1}
