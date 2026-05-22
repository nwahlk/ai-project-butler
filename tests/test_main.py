from pathlib import Path

from typer.testing import CliRunner

from telemetry import AnalyzerExecution, AnalyzerFailure, ExecutionReport
from cli import app
from config import ScanConfig
from project import build_project_execution, build_project_report
from reporters.execution import render_execution_report
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


def test_build_project_execution_returns_report_and_execution_telemetry(
    tmp_path: Path,
):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("# TODO: add cli\n", encoding="utf-8")

    execution = build_project_execution(ScanConfig(root=tmp_path))

    assert execution.report.total_files == 2
    assert execution.execution.root == tmp_path.resolve()
    assert execution.execution.total_files == 2
    assert execution.execution.total_duration_ms >= 0
    assert execution.execution.scan_duration_ms >= 0
    assert execution.execution.analysis_duration_ms >= 0
    assert [item.name for item in execution.execution.analyzers] == [
        "file_types",
        "markers",
        "todos",
    ]


def test_render_execution_report_shows_analyzer_timings(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    execution = build_project_execution(ScanConfig(root=tmp_path))

    table = render_execution_report(execution.execution)

    assert [column.header for column in table.columns] == [
        "Analyzer",
        "Status",
        "Time",
        "Error",
    ]
    assert table.row_count == 3


def test_render_execution_report_includes_failed_analyzer_error(tmp_path: Path):
    table = render_execution_report(
        ExecutionReport(
            root=tmp_path,
            total_duration_ms=1,
            scan_duration_ms=0,
            analysis_duration_ms=1,
            total_files=0,
            analyzers=[
                AnalyzerExecution(
                    name="todos",
                    status="failed",
                    duration_ms=1,
                    failure=AnalyzerFailure(
                        analyzer="todos",
                        error_type="RuntimeError",
                        message="boom",
                    ),
                )
            ],
        )
    )

    assert table.row_count == 1
    assert table.columns[1]._cells == ["FAILED"]
    assert table.columns[3]._cells == ["RuntimeError: boom"]


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
    assert "INFO " not in result.output


def test_cli_execution_report_shows_analyzer_timing_table(
    tmp_path: Path,
    monkeypatch,
):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["project-butler", "scan", str(tmp_path), "--execution-report"],
    )

    result = runner.invoke(app, ["scan", str(tmp_path), "--execution-report"])

    assert result.exit_code == 0
    assert "Project Butler Report" in result.output
    assert "Analyzer" in result.output
    assert "Status" in result.output
    assert "Time" in result.output
    assert "Error" in result.output
    assert "TODOAnalyzer" in result.output
