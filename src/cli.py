import sys
from pathlib import Path

import typer
from rich.console import Console

from config import ScanConfig
from logging_utils import get_logger, setup_logging
from project import build_project_execution, build_project_report
from reporters.execution import render_execution_report
from reporters.terminal import render_terminal_report


logger = get_logger(__name__)
app = typer.Typer(help="Scan a code project and print a lightweight report.")
console = Console()


def _has_cli_flag(*names: str) -> bool:
    return any(arg in names for arg in sys.argv[1:])


@app.callback()
def main() -> None:
    """Project Butler command line interface."""


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Project directory to scan."),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show info logs.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show debug logs.",
    ),
    execution_report: bool = typer.Option(
        False,
        "--execution-report",
        help="Show analyzer execution timing.",
    ),
) -> None:
    debug_enabled = debug is True or _has_cli_flag("--debug")
    verbose_enabled = verbose is True or _has_cli_flag("--verbose", "-v")
    execution_report_enabled = (
        execution_report is True or _has_cli_flag("--execution-report")
    )
    setup_logging(verbose=verbose_enabled, debug=debug_enabled)
    logger.info("Scanning project at %s", path)

    if execution_report_enabled:
        execution = build_project_execution(ScanConfig(root=path))
        report = execution.report
    else:
        execution = None
        report = build_project_report(ScanConfig(root=path))

    console.print(render_terminal_report(report), markup=False)
    if execution is not None:
        console.print()
        console.print(render_execution_report(execution.execution))


if __name__ == "__main__":
    app()
