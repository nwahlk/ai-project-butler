import logging
from pathlib import Path

from analyzers.base import AnalysisContext
from analyzers.runner import run_analyzers, run_analyzers_with_telemetry
from config import AnalyzerConfig, ScanConfig
from analyzers.file_types import count_file_types
from analyzers.todos import find_todos, find_todos_in_text
from models import ProjectAnalysis, ScanResult, ScannedFile
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


def test_run_analyzers_with_telemetry_records_analyzer_execution(tmp_path: Path):
    path = tmp_path / "app.py"
    path.write_text("# TODO: add cli\n", encoding="utf-8")
    scan_result = ScanResult(
        root=tmp_path,
        files=[
            ScannedFile(
                path=path,
                relative_path=Path("app.py"),
                suffix=".py",
                size=path.stat().st_size,
            )
        ],
    )

    analysis, executions = run_analyzers_with_telemetry(
        scan_result,
        AnalyzerConfig(enabled=("file_types", "todos")),
    )

    assert analysis.file_types == {".py": 1}
    assert len(analysis.todos) == 1
    assert [execution.name for execution in executions] == ["file_types", "todos"]
    assert all(execution.status == "ok" for execution in executions)
    assert all(execution.duration_ms >= 0 for execution in executions)
    assert executions[0].result_summary["file_types"] == 1
    assert executions[1].result_summary["todos"] == 1


def test_run_analyzers_with_telemetry_records_failure_and_continues(
    tmp_path: Path,
    caplog,
):
    class FailingAnalyzer:
        name = "failing"

        def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
            raise RuntimeError("boom")

    class PassingAnalyzer:
        name = "passing"

        def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
            return ProjectAnalysis(file_types={".py": 1})

    caplog.set_level(logging.ERROR, logger="analyzers.runner")
    scan_result = ScanResult(root=tmp_path, files=[])

    analysis, executions = run_analyzers_with_telemetry(
        scan_result,
        AnalyzerConfig(enabled=("failing", "passing")),
        analyzers=(FailingAnalyzer(), PassingAnalyzer()),
    )

    assert analysis.file_types == {".py": 1}
    assert [execution.name for execution in executions] == ["failing", "passing"]
    assert executions[0].status == "failed"
    assert executions[0].failure is not None
    assert executions[0].failure.error_type == "RuntimeError"
    assert executions[0].failure.message == "boom"
    assert executions[0].failure.recoverable is True
    assert executions[1].status == "ok"
    assert "[FailingAnalyzer] failed in" in caplog.text


def test_run_analyzers_does_not_catch_keyboard_interrupt(tmp_path: Path):
    class InterruptingAnalyzer:
        name = "interrupting"

        def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
            raise KeyboardInterrupt()

    scan_result = ScanResult(root=tmp_path, files=[])

    try:
        run_analyzers_with_telemetry(
            scan_result,
            AnalyzerConfig(enabled=("interrupting",)),
            analyzers=(InterruptingAnalyzer(),),
        )
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("Expected KeyboardInterrupt")
