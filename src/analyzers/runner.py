from collections.abc import Iterable
from typing import TypeVar

from analyzers.base import AnalysisContext, Analyzer
from analyzers.file_types import FileTypeAnalyzer
from analyzers.markers import MarkerAnalyzer
from analyzers.todos import TodoAnalyzer
from config import AnalyzerConfig
from models import ProjectAnalysis, ScanResult


Value = TypeVar("Value")

DEFAULT_ANALYZERS: tuple[Analyzer, ...] = (
    FileTypeAnalyzer(),
    MarkerAnalyzer(),
    TodoAnalyzer(),
)


def run_analyzers(
    scan_result: ScanResult,
    config: AnalyzerConfig,
    analyzers: Iterable[Analyzer] = DEFAULT_ANALYZERS,
) -> ProjectAnalysis:
    available = {analyzer.name: analyzer for analyzer in analyzers}
    unknown = [name for name in config.enabled if name not in available]
    if unknown:
        names = ", ".join(unknown)
        raise ValueError(f"Unknown analyzer(s): {names}")

    context = AnalysisContext(
        root=scan_result.root,
        files=scan_result.files,
        config=config,
    )
    results = [available[name].analyze(context) for name in config.enabled]

    return ProjectAnalysis(
        file_types=_merge_dicts(result.file_types for result in results),
        markers=_merge_dicts(result.markers for result in results),
        todos=[
            todo
            for result in results
            for todo in result.todos
        ],
    )


def _merge_dicts(items: Iterable[dict[str, Value]]) -> dict[str, Value]:
    merged: dict[str, Value] = {}
    for item in items:
        merged.update(item)
    return merged
