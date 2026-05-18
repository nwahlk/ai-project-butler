from pathlib import Path

from cli import app
from config import ScanConfig
from reporters.terminal import render_terminal_report
from scanner import build_project_report


def scan_project(path: str):
    """Backward-compatible wrapper for older imports."""
    return render_terminal_report(build_project_report(ScanConfig(root=Path(path))))


if __name__ == "__main__":
    app()
