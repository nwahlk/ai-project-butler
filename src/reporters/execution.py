from rich import box
from rich.table import Table

from telemetry import ExecutionReport


def render_execution_report(report: ExecutionReport) -> Table:
    table = Table(box=box.HEAVY)
    table.add_column("Analyzer")
    table.add_column("Status")
    table.add_column("Time", justify="right")
    table.add_column("Error")

    for analyzer in report.analyzers:
        table.add_row(
            _display_name(analyzer.name),
            analyzer.status.upper(),
            f"{analyzer.duration_ms / 1000:.2f}s",
            _error_text(analyzer),
        )

    return table


def _display_name(name: str) -> str:
    names = {
        "file_types": "FileTypeAnalyzer",
        "markers": "MarkerAnalyzer",
        "todos": "TODOAnalyzer",
    }
    return names.get(name, name)


def _error_text(analyzer) -> str:
    if analyzer.failure is None:
        return ""
    return f"{analyzer.failure.error_type}: {analyzer.failure.message}"
