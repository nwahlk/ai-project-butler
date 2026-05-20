from pathlib import Path

from analyzers.base import AnalysisContext
from models import ProjectAnalysis


README_NAMES = ("README", "README.md", "README.rst", "README.txt")


def check_project_markers(root: Path, markers: tuple[str, ...]) -> dict[str, bool]:
    result: dict[str, bool] = {}

    for marker in markers:
        if marker == "README":
            result[marker] = any((root / name).is_file() for name in README_NAMES)
        else:
            result[marker] = (root / marker).is_file()

    return result


class MarkerAnalyzer:
    name = "markers"

    def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
        return ProjectAnalysis(
            markers=check_project_markers(context.root, context.config.markers)
        )
