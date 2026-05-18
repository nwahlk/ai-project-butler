from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanConfig:
    root: Path
    exclude_dirs: tuple[str, ...]
    markers: tuple[str, ...]
    todo_keywords: tuple[str, ...]


@dataclass(frozen=True)
class ScannedFile:
    path: Path
    relative_path: Path
    suffix: str
    size: int


@dataclass(frozen=True)
class TodoItem:
    path: Path
    relative_path: Path
    line_number: int
    keyword: str
    text: str


@dataclass(frozen=True)
class ProjectReport:
    root: Path
    total_files: int
    file_types: dict[str, int]
    markers: dict[str, bool]
    todos: list[TodoItem]
