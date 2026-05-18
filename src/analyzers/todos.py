import logging
import re

from models import ScannedFile, TodoItem


logger = logging.getLogger(__name__)
COMMENT_MARKERS = ("#", "//", "/*", "<!--", "--", ";", "*")


def _compile_keyword_pattern(keywords: tuple[str, ...]) -> re.Pattern[str]:
    keyword_group = "|".join(re.escape(keyword) for keyword in keywords)
    return re.compile(rf"\b({keyword_group})\b(?=[:\s-])")


def _find_unquoted_marker(line: str) -> int | None:
    quote: str | None = None
    escaped = False

    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char in ("'", '"'):
            quote = char
            continue

        for marker in COMMENT_MARKERS:
            if line.startswith(marker, index):
                return index

    return None


def _todo_search_text(line: str) -> tuple[str, bool] | None:
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped[2:].lstrip(), False

    marker_index = _find_unquoted_marker(line)
    if marker_index is not None:
        return line[marker_index:], True

    return stripped, False


def find_todos(files: list[ScannedFile], keywords: tuple[str, ...]) -> list[TodoItem]:
    items: list[TodoItem] = []
    pattern = _compile_keyword_pattern(keywords)

    for file in files:
        try:
            lines = file.path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            logger.debug("Skipping unreadable file %s: %s", file.path, exc)
            continue

        for line_number, line in enumerate(lines, start=1):
            search_target = _todo_search_text(line)
            if search_target is None:
                continue

            search_text, allow_inline = search_target
            match = pattern.search(search_text) if allow_inline else pattern.match(search_text)
            if match:
                items.append(
                    TodoItem(
                        path=file.path,
                        relative_path=file.relative_path,
                        line_number=line_number,
                        keyword=match.group(1),
                        text=line.strip(),
                    )
                )

    return items
