from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from config import AnalyzerConfig
from models import ProjectAnalysis, ScannedFile


@dataclass(frozen=True)
class AnalysisContext:
    root: Path
    files: list[ScannedFile]
    config: AnalyzerConfig


class Analyzer(Protocol):
    name: str

    def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
        ...
