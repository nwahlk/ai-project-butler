from collections.abc import Iterable
from typing import TypeVar

from analyzers.base import AnalysisContext, Analyzer
from analyzers.file_types import FileTypeAnalyzer
from analyzers.markers import MarkerAnalyzer
from analyzers.todos import TodoAnalyzer
from config import AnalyzerConfig
from logging_utils import get_logger
from models import ProjectAnalysis, ScanResult
from telemetry import (
    AnalyzerExecution,
    AnalyzerFailure,
    elapsed_ms,
    now_ms,
    summarize_analysis,
)


Value = TypeVar("Value")
logger = get_logger(__name__)

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
    analysis, _ = run_analyzers_with_telemetry(scan_result, config, analyzers)
    return analysis


def run_analyzers_with_telemetry(
    scan_result: ScanResult,
    config: AnalyzerConfig,
    analyzers: Iterable[Analyzer] = DEFAULT_ANALYZERS,
) -> tuple[ProjectAnalysis, list[AnalyzerExecution]]:
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
    results: list[ProjectAnalysis] = []
    executions: list[AnalyzerExecution] = []

    logger.info("Analysis started analyzers=%s", ",".join(config.enabled))
    for name in config.enabled:
        analyzer = available[name]
        display_name = _display_name(analyzer)
        start_ms = now_ms()
        logger.info("[%s] started", display_name)
        logger.info("[%s] scanned %s files", display_name, len(context.files))
        try:
            result = analyzer.analyze(context)
        except Exception as exc:
            duration_ms = elapsed_ms(start_ms)
            failure = AnalyzerFailure(
                analyzer=name,
                error_type=exc.__class__.__name__,
                message=str(exc),
                recoverable=True,
            )
            executions.append(
                AnalyzerExecution(
                    name=name,
                    status="failed",
                    duration_ms=duration_ms,
                    failure=failure,
                )
            )
            logger.exception(
                "[%s] failed in %.2fs",
                display_name,
                duration_ms / 1000,
            )
            continue

        duration_ms = elapsed_ms(start_ms)
        summary = summarize_analysis(result)
        found_count, found_label = _found_summary(name, summary)
        executions.append(
            AnalyzerExecution(
                name=name,
                status="ok",
                duration_ms=duration_ms,
                result_summary=summary,
            )
        )
        results.append(result)
        logger.info("[%s] found %s %s", display_name, found_count, found_label)
        logger.info("[%s] completed in %.2fs", display_name, duration_ms / 1000)

    analysis = ProjectAnalysis(
        file_types=_merge_dicts(result.file_types for result in results),
        markers=_merge_dicts(result.markers for result in results),
        todos=[
            todo
            for result in results
            for todo in result.todos
        ],
    )
    return analysis, executions


def _merge_dicts(items: Iterable[dict[str, Value]]) -> dict[str, Value]:
    merged: dict[str, Value] = {}
    for item in items:
        merged.update(item)
    return merged


def _display_name(analyzer: Analyzer) -> str:
    class_name = analyzer.__class__.__name__
    if class_name == "TodoAnalyzer":
        return "TODOAnalyzer"
    return class_name


def _found_summary(name: str, summary: dict[str, int]) -> tuple[int, str]:
    if name == "file_types":
        return summary["file_types"], "file types"
    if name == "markers":
        return summary["markers"], "markers"
    if name == "todos":
        return summary["todos"], "TODOs"
    return sum(summary.values()), "items"
