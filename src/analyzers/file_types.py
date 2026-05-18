from collections import Counter

from models import ScannedFile


def count_file_types(files: list[ScannedFile]) -> dict[str, int]:
    counts = Counter(file.suffix or "[no extension]" for file in files)
    return dict(counts)
