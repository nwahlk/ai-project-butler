import logging
from pathlib import Path

import typer
from rich.console import Console

from config import ScanConfig
from logging_config import setup_logging
from project import build_project_report
from reporters.terminal import render_terminal_report


logger = logging.getLogger(__name__)
app = typer.Typer(help="Scan a code project and print a lightweight report.")
console = Console()


@app.callback()
def main() -> None:
    """Project Butler command line interface."""


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Project directory to scan."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show info logs."),
    debug: bool = typer.Option(False, "--debug", help="Show debug logs."),
) -> None:
    setup_logging(verbose=verbose, debug=debug)
    logger.info("Scanning project at %s", path)

    report = build_project_report(ScanConfig(root=path))
    console.print(render_terminal_report(report), markup=False)


if __name__ == "__main__":
    app()
