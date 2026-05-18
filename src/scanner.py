import logging
import os
from pathlib import Path

from analyzers.file_types import count_file_types
from analyzers.markers import check_project_markers
from analyzers.todos import find_todos
from config import ScanConfig
from models import ProjectReport, ScannedFile


logger = logging.getLogger(__name__)


def scan_project_files(config: ScanConfig) -> list[ScannedFile]:
    if not config.root.exists():
        raise FileNotFoundError(f"Project path does not exist: {config.root}")
    if not config.root.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {config.root}")

    files: list[ScannedFile] = []

    for dirpath, dirnames, filenames in os.walk(config.root):
        dirnames[:] = [name for name in dirnames if name not in config.exclude_dirs]
        current_dir = Path(dirpath)

        for filename in filenames:
            path = current_dir / filename
            try:
                stat = path.stat()
            except OSError as exc:
                logger.debug("Skipping inaccessible file %s: %s", path, exc)
                continue

            files.append(
                ScannedFile(
                    path=path,
                    relative_path=path.relative_to(config.root),
                    suffix=path.suffix.lower(),
                    size=stat.st_size,
                )
            )

    return files


def build_project_report(config: ScanConfig) -> ProjectReport:
    files = scan_project_files(config)

    return ProjectReport(
        root=config.root,
        total_files=len(files),
        file_types=count_file_types(files),
        markers=check_project_markers(config.root, config.markers),
        todos=find_todos(files, config.todo_keywords),
    )
