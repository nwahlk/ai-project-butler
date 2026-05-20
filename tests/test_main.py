from pathlib import Path

from typer.testing import CliRunner

from cli import app
from config import ScanConfig
from project import build_project_report
from reporters.terminal import render_terminal_report
from scanner import scan_project_files

runner = CliRunner()


def test_build_project_report_counts_files_and_detects_markers(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("# TODO: add cli\nprint('hi')\n", encoding="utf-8")
    (tmp_path / "config.py").write_text('KEYWORDS = ("TODO", "FIXME")\n', encoding="utf-8")
    (tmp_path / ".env").mkdir()
    (tmp_path / ".env" / "ignored.py").write_text("print('ignore')\n", encoding="utf-8")

    report = build_project_report(ScanConfig(root=tmp_path))

    assert report.total_files == 4
    assert report.file_types == {".md": 1, ".txt": 1, ".py": 2}
    assert report.markers["README"] is True
    assert report.markers["requirements.txt"] is True
    assert report.markers["Dockerfile"] is False
    assert len(report.todos) == 1
    assert report.todos[0].relative_path == Path("app.py")
    assert report.todos[0].line_number == 1


def test_render_terminal_report_is_presentation_only(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    report = build_project_report(ScanConfig(root=tmp_path))

    output = render_terminal_report(report)

    assert "Project Butler Report" in output
    assert "Total files: 1" in output
    assert "README: OK" in output


def test_scan_project_files_excludes_configured_directories(tmp_path: Path):
    (tmp_path / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "ignored").mkdir()
    (tmp_path / "ignored" / "secret.py").write_text("print('skip')\n", encoding="utf-8")

    files = scan_project_files(ScanConfig(root=tmp_path, exclude_dirs=("ignored",)))

    assert [file.relative_path for file in files] == [Path("app.py")]


def test_scan_project_files_rejects_missing_path(tmp_path: Path):
    missing_path = tmp_path / "missing"

    try:
        scan_project_files(ScanConfig(root=missing_path))
    except FileNotFoundError as exc:
        assert str(missing_path.resolve()) in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_cli_exposes_scan_subcommand(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert "Project Butler Report" in result.output
