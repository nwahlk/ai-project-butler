from dataclasses import dataclass, field
from pathlib import Path

from models import ProjectAnalysis, ProjectReport


@dataclass(frozen=True)
class AnalyzerFailure:
    analyzer: str
    error_type: str
    message: str
    recoverable: bool = True


@dataclass(frozen=True)
class AnalyzerExecution:
    name: str
    status: str
    duration_ms: float
    failure: AnalyzerFailure | None = None
    result_summary: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionReport:
    root: Path
    total_duration_ms: float
    scan_duration_ms: float
    analysis_duration_ms: float
    total_files: int
    analyzers: list[AnalyzerExecution]


@dataclass(frozen=True)
class ProjectExecution:
    report: ProjectReport
    execution: ExecutionReport


def summarize_analysis(analysis: ProjectAnalysis) -> dict[str, int]:
    return {
        "file_types": len(analysis.file_types),
        "markers": len(analysis.markers),
        "todos": len(analysis.todos),
    }
