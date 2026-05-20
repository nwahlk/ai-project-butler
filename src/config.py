from dataclasses import dataclass
from pathlib import Path

from models import ScanConfig as BaseScanConfig


DEFAULT_EXCLUDE_DIRS = (
    ".git",
    ".env",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".aider.tags.cache.v4",
    "node_modules",
    "dist",
    "build",
)

DEFAULT_MARKERS = (
    "README",
    "Dockerfile",
    "requirements.txt",
    "package.json",
)

DEFAULT_TODO_KEYWORDS = (
    "TODO",
    "FIXME",
)

DEFAULT_ANALYZERS = (
    "file_types",
    "markers",
    "todos",
)


@dataclass(frozen=True)
class ScanConfig(BaseScanConfig):
    root: Path
    exclude_dirs: tuple[str, ...] = DEFAULT_EXCLUDE_DIRS

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).resolve())


@dataclass(frozen=True)
class AnalyzerConfig:
    enabled: tuple[str, ...] = DEFAULT_ANALYZERS
    markers: tuple[str, ...] = DEFAULT_MARKERS
    todo_keywords: tuple[str, ...] = DEFAULT_TODO_KEYWORDS
