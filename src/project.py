from analyzers.runner import run_analyzers
from config import AnalyzerConfig, ScanConfig
from models import ProjectReport
from scanner import scan_project


def build_project_report(
    config: ScanConfig,
    analyzer_config: AnalyzerConfig | None = None,
) -> ProjectReport:
    scan_result = scan_project(config)
    analysis = run_analyzers(
        scan_result=scan_result,
        config=analyzer_config or AnalyzerConfig(),
    )

    return ProjectReport(
        root=config.root,
        total_files=len(scan_result.files),
        analysis=analysis,
    )
