from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ScanConfig:
    root: Path
    exclude_dirs: tuple[str, ...]


@dataclass(frozen=True)
class ScannedFile:
    path: Path
    relative_path: Path
    suffix: str
    size: int


@dataclass(frozen=True)
class ScanResult:
    root: Path
    files: list[ScannedFile]


@dataclass(frozen=True)
class TodoItem:
    path: Path
    relative_path: Path
    line_number: int
    keyword: str
    text: str


@dataclass(frozen=True)
class ProjectAnalysis:
    file_types: dict[str, int] = field(default_factory=dict)
    markers: dict[str, bool] = field(default_factory=dict)
    todos: list[TodoItem] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectReport:
    root: Path
    total_files: int
    analysis: ProjectAnalysis = field(default_factory=ProjectAnalysis)

    @property
    def file_types(self) -> dict[str, int]:
        return self.analysis.file_types

    @property
    def markers(self) -> dict[str, bool]:
        return self.analysis.markers

    @property
    def todos(self) -> list[TodoItem]:
        return self.analysis.todos
