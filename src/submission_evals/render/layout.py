from __future__ import annotations

from collections.abc import Sequence

WIDTH = 96


def rule(char: str = "=") -> str:
    return char * WIDTH


def band(title: str) -> str:
    return f"{title.upper()} ".ljust(WIDTH, "-")


def centred(text: str) -> str:
    return text.center(WIDTH).rstrip()


def box(checked: bool) -> str:
    return "[X]" if checked else "[ ]"


def cell(label: str, value: object, width: int) -> str:
    text = str(value)
    if not label:
        return text.ljust(width)
    if not text:
        return f"{label}:".ljust(width)
    return f"{label}: {text}".ljust(width)


def ticked(checked: bool, label: str, width: int) -> str:
    return f"{box(checked)} {label}".ljust(width)


def row(*cells: str) -> str:
    return "".join(cells).rstrip()


def money(amount: int | None) -> str:
    return "" if amount is None else f"{amount:,}"


def table_header(columns: Sequence[tuple[str, int]]) -> list[str]:
    heading = "".join(name[: width - 1].ljust(width) for name, width in columns).rstrip()
    return [heading, "-" * sum(width for _, width in columns)]


def table_row(values: Sequence[object], columns: Sequence[tuple[str, int]]) -> str:
    parts = []
    for value, (_, width) in zip(values, columns, strict=True):
        text = str(value)
        parts.append(text[: width - 1].ljust(width))
    return "".join(parts).rstrip()


def wrap(text: str, indent: str = "") -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = indent
    for word in words:
        candidate = f"{current}{word} " if current.strip() else f"{indent}{word} "
        if len(candidate.rstrip()) > WIDTH:
            lines.append(current.rstrip())
            current = f"{indent}{word} "
        else:
            current = candidate
    if current.strip():
        lines.append(current.rstrip())
    return lines


SYNTHETIC_FOOTER = (
    "SYNTHETIC DOCUMENT. Generated for an evaluation set. Not an ACORD form and not "
    "produced by, affiliated with or endorsed by ACORD. Field names follow industry "
    "usage. No real applicant, carrier or policy is described."
)


def document(lines: list[str]) -> str:
    return "\n".join(line.rstrip(" \t") for line in lines) + "\n"


def footer(form_name: str) -> list[str]:
    return [rule("-"), *wrap(SYNTHETIC_FOOTER), f"{form_name} (synthetic)"]
