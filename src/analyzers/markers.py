from pathlib import Path


README_NAMES = ("README", "README.md", "README.rst", "README.txt")


def check_project_markers(root: Path, markers: tuple[str, ...]) -> dict[str, bool]:
    result: dict[str, bool] = {}

    for marker in markers:
        if marker == "README":
            result[marker] = any((root / name).is_file() for name in README_NAMES)
        else:
            result[marker] = (root / marker).is_file()

    return result
