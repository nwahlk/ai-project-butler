from models import ProjectReport


def render_terminal_report(report: ProjectReport) -> str:
    lines = [
        "Project Butler Report",
        f"Root: {report.root}",
        f"Total files: {report.total_files}",
        "",
        "File types:",
    ]

    if report.file_types:
        for suffix, count in sorted(report.file_types.items()):
            lines.append(f"  {suffix}: {count}")
    else:
        lines.append("  none")

    lines.extend(["", "Project markers:"])
    for marker, exists in report.markers.items():
        status = "OK" if exists else "MISSING"
        lines.append(f"  {marker}: {status}")

    lines.extend(["", "TODO/FIXME:"])
    if report.todos:
        for item in report.todos:
            lines.append(
                f"  {item.relative_path}:{item.line_number} "
                f"[{item.keyword}] {item.text}"
            )
    else:
        lines.append("  none")

    return "\n".join(lines)
