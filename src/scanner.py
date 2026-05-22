import os
from pathlib import Path

from config import ScanConfig
from logging_utils import get_logger
from models import ScannedFile, ScanResult
from telemetry import elapsed_ms, now_ms


logger = get_logger(__name__)


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


def scan_project(config: ScanConfig) -> ScanResult:
    start_ms = now_ms()
    logger.info("Scan started root=%s", config.root)
    files = scan_project_files(config)
    logger.info(
        "Scan finished root=%s files=%s duration_ms=%.2f",
        config.root,
        len(files),
        elapsed_ms(start_ms),
    )
    return ScanResult(root=config.root, files=files)
