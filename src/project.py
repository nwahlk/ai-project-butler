from analyzers.runner import run_analyzers_with_telemetry
from config import AnalyzerConfig, ScanConfig
from logging_utils import get_logger
from models import ProjectReport
from scanner import scan_project
from telemetry import ExecutionReport, ProjectExecution, elapsed_ms, now_ms


logger = get_logger(__name__)


def build_project_execution(
    config: ScanConfig,
    analyzer_config: AnalyzerConfig | None = None,
) -> ProjectExecution:
    resolved_analyzer_config = analyzer_config or AnalyzerConfig()
    total_start_ms = now_ms()
    logger.info("Project pipeline started root=%s", config.root)

    scan_start_ms = now_ms()
    scan_result = scan_project(config)
    scan_duration_ms = elapsed_ms(scan_start_ms)

    analysis_start_ms = now_ms()
    analysis, analyzer_executions = run_analyzers_with_telemetry(
        scan_result=scan_result,
        config=resolved_analyzer_config,
    )
    analysis_duration_ms = elapsed_ms(analysis_start_ms)

    report = ProjectReport(
        root=config.root,
        total_files=len(scan_result.files),
        analysis=analysis,
    )
    execution = ExecutionReport(
        root=config.root,
        total_duration_ms=elapsed_ms(total_start_ms),
        scan_duration_ms=scan_duration_ms,
        analysis_duration_ms=analysis_duration_ms,
        total_files=len(scan_result.files),
        analyzers=analyzer_executions,
    )
    logger.info(
        "Project pipeline finished root=%s total_files=%s total_duration_ms=%.2f",
        config.root,
        len(scan_result.files),
        execution.total_duration_ms,
    )

    return ProjectExecution(report=report, execution=execution)


def build_project_report(
    config: ScanConfig,
    analyzer_config: AnalyzerConfig | None = None,
) -> ProjectReport:
    return build_project_execution(config, analyzer_config).report
