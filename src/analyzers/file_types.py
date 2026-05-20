from collections import Counter
from collections.abc import Iterable

from analyzers.base import AnalysisContext
from models import ProjectAnalysis, ScannedFile


def count_file_types(files: Iterable[ScannedFile]) -> dict[str, int]:
    counts = Counter(file.suffix or "[no extension]" for file in files)
    return dict(counts)


class FileTypeAnalyzer:
    name = "file_types"

    def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
        return ProjectAnalysis(file_types=count_file_types(context.files))
