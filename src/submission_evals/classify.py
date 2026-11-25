from __future__ import annotations

import io
import re

from submission_evals.truth import DocumentName

_SIGNALS: tuple[tuple[DocumentName, tuple[str, ...], int], ...] = (
    (DocumentName.APPLICATION, ("applicant information section", "chk here if none"), 6),
    (DocumentName.APPLICATION, ("commercial insurance application", "loss history"), 5),
    (DocumentName.PROPERTY_SECTION, ("property section", "subject of insurance", "coins"), 5),
    (DocumentName.LIABILITY_SECTION, ("general liability section", "schedule of hazards"), 5),
    (DocumentName.SOV, ("statement of values", "business personal property"), 5),
    (DocumentName.LOSS_RUN_A, ("claims experience report", "valuation date"), 5),
    (DocumentName.LOSS_RUN_B, ("loss experience listing", "evaluated as of"), 5),
    (DocumentName.LOSS_RUN_A, ("date of loss", "incurred", "claim number"), 4),
    (DocumentName.LOSS_RUN_B, ("date of occurrence", "outstanding", "claim no"), 4),
    (DocumentName.NO_LOSSES_LETTER, ("no claims have been", "to whom it may concern"), 5),
    (DocumentName.BROKER_EMAIL, ("subject:", "from:", "to:"), 4),
    (DocumentName.RECORDS_ON_FILE, ("submissions already on file",), 6),
    (DocumentName.SLIP, ("market reform contract", "unique market reference"), 6),
    (DocumentName.SLIP, ("risk details", "security details", "order hereon"), 5),
)

_BY_NAME = {name.value: name for name in DocumentName}


def text_from(filename: str, raw: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            return "\n\f".join(page.extract_text() or "" for page in reader.pages)
        except Exception:  # noqa: BLE001
            return ""
    return raw.decode("utf-8", errors="replace")


def by_filename(filename: str) -> DocumentName | None:
    stem = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    return _BY_NAME.get(stem)


def by_content(body: str) -> tuple[DocumentName | None, int]:
    haystack = re.sub(r"\s+", " ", body[:12_000].lower())
    best: tuple[DocumentName | None, int] = (None, 0)
    for name, phrases, weight in _SIGNALS:
        hits = sum(1 for phrase in phrases if phrase in haystack)
        if hits == 0:
            continue
        score = weight * hits // len(phrases) + hits
        if score > best[1]:
            best = (name, score)
    return best


def classify(filename: str, raw: bytes) -> tuple[DocumentName | None, str, str]:
    body = text_from(filename, raw)
    if not body.strip():
        return None, "", "could not read any text out of it"
    named = by_filename(filename)
    if named is not None:
        return named, body, "matched on filename"
    guessed, score = by_content(body)
    if guessed is None:
        return None, body, "could not tell what kind of document this is"
    return guessed, body, f"recognised from its contents (confidence {score})"


def assign(uploads: list[tuple[str, bytes]]) -> tuple[dict[DocumentName, str], list[dict]]:
    packet: dict[DocumentName, str] = {}
    report: list[dict] = []
    spare = [DocumentName.LOSS_RUN_B, DocumentName.LOSS_RUN_A]
    for filename, raw in uploads:
        name, body, why = classify(filename, raw)
        if name is None:
            report.append({"filename": filename, "as": None, "why": why})
            continue
        if name in packet and name in (DocumentName.LOSS_RUN_A, DocumentName.LOSS_RUN_B):
            alternative = next((n for n in spare if n not in packet), None)
            if alternative is not None:
                name = alternative
        if name in packet:
            report.append(
                {"filename": filename, "as": None, "why": f"already have a {name.value}"}
            )
            continue
        packet[name] = body
        report.append({"filename": filename, "as": name.value, "why": why})
    return packet, report
