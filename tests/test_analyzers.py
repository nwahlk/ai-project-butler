from pathlib import Path

from analyzers.runner import run_analyzers
from config import AnalyzerConfig, ScanConfig
from analyzers.file_types import count_file_types
from analyzers.todos import find_todos, find_todos_in_text
from models import ScanResult, ScannedFile
from project import build_project_report


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


def test_build_project_report_respects_enabled_analyzers(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("# TODO: add cli\n", encoding="utf-8")

    report = build_project_report(
        ScanConfig(root=tmp_path),
        AnalyzerConfig(enabled=("file_types",)),
    )

    assert report.file_types == {".md": 1, ".py": 1}
    assert report.markers == {}
    assert report.todos == []


def test_run_analyzers_rejects_unknown_analyzer(tmp_path: Path):
    scan_result = ScanResult(root=tmp_path, files=[])

    try:
        run_analyzers(scan_result, AnalyzerConfig(enabled=("missing",)))
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
