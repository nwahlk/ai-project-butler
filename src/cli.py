import logging
from pathlib import Path

import typer
from rich import print as rprint

from config import ScanConfig
from logging_config import setup_logging
from reporters.terminal import render_terminal_report
from scanner import build_project_report


logger = logging.getLogger(__name__)
app = typer.Typer(help="Scan a code project and print a lightweight report.")


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
    rprint(render_terminal_report(report))


if __name__ == "__main__":
    app()
