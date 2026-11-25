from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from submission_evals.extract import (
    DEFAULT_SOURCES,
    GRADED_FIELDS,
    LITERAL_CHECK_EXEMPT,
    Answer,
    ExtractedSubmission,
)
from submission_evals.grade import appears_as_token, is_nil, normalise_money, renderings
from submission_evals.truth import DocumentName, SourceMode

Severity = Literal["blocking", "query", "note"]


class Finding(BaseModel):
    check: str
    severity: Severity
    field: str | None
    message: str
    evidence: list[str] = []


def _answers(produced: ExtractedSubmission) -> dict[str, Answer]:
    return {field: getattr(produced, field) for field in GRADED_FIELDS}


def citation_resolves(
    produced: ExtractedSubmission, packet: dict[DocumentName, str]
) -> list[Finding]:
    findings = []
    for field, answer in _answers(produced).items():
        if answer.flagged:
            continue
        source = answer.source
        if source is None:
            findings.append(
                Finding(
                    check="citation_missing",
                    severity="blocking",
                    field=field,
                    message="Recorded a value with no source at all.",
                )
            )
        elif source.document not in packet:
            findings.append(
                Finding(
                    check="citation_unresolvable",
                    severity="blocking",
                    field=field,
                    message=(
                        f"Cites {source.document.value}, which is not in this packet."
                    ),
                )
            )
    return findings


def citation_is_honest(
    produced: ExtractedSubmission, packet: dict[DocumentName, str]
) -> list[Finding]:
    findings = []
    for field, answer in _answers(produced).items():
        if (
            answer.flagged
            or answer.mode != SourceMode.READ
            or is_nil(answer.value)
            or field in LITERAL_CHECK_EXEMPT
        ):
            continue
        source = answer.source
        if source is None or source.document not in packet:
            continue
        body = packet[source.document]
        if not any(appears_as_token(form, body) for form in renderings(field, answer.value)):
            findings.append(
                Finding(
                    check="citation_not_supported",
                    severity="blocking",
                    field=field,
                    message=(
                        f"Says it read {answer.value!r} from {source.document.value}, "
                        "but that value does not appear in it."
                    ),
                    evidence=[source.locator],
                )
            )
    return findings


def derived_shows_its_working(produced: ExtractedSubmission) -> list[Finding]:
    return [
        Finding(
            check="derived_without_inputs",
            severity="query",
            field=field,
            message="Worked this out but did not say what from, so nobody can re-check it.",
        )
        for field, answer in _answers(produced).items()
        if not answer.flagged and answer.mode == SourceMode.DERIVED and not answer.derived_from
    ]


def loss_rows_reconcile(produced: ExtractedSubmission) -> list[Finding]:
    findings = []
    for row in produced.losses:
        if row.paid_usd + row.reserved_usd != row.incurred_usd:
            findings.append(
                Finding(
                    check="loss_row_does_not_reconcile",
                    severity="blocking",
                    field=None,
                    message=(
                        f"Claim {row.claim_no}: paid {row.paid_usd:,} plus reserved "
                        f"{row.reserved_usd:,} is {row.paid_usd + row.reserved_usd:,}, "
                        f"not the {row.incurred_usd:,} incurred. A column is mislabelled."
                    ),
                    evidence=[row.claim_no],
                )
            )
    return findings


def _number(answer: Answer) -> int | None:
    return None if answer.flagged else normalise_money(answer.value)


def totals_match_the_rows(produced: ExtractedSubmission) -> list[Finding]:
    answers = _answers(produced)
    findings = []

    pairs = (
        ("loss_count_5y", len(produced.losses), "claims"),
        ("location_count", len(produced.locations), "locations"),
        (
            "total_paid_5y_usd",
            sum(row.paid_usd for row in produced.losses),
            "paid across the claim rows",
        ),
        (
            "total_incurred_5y_usd",
            sum(row.incurred_usd for row in produced.losses),
            "incurred across the claim rows",
        ),
        (
            "total_insured_value_usd",
            sum(
                row.building_value_usd + row.bpp_value_usd + row.business_income_value_usd
                for row in produced.locations
            ),
            "values across the location rows",
        ),
    )
    for field, from_rows, label in pairs:
        stated = _number(answers[field])
        if stated is None or not produced.losses and "claim" in label:
            continue
        if field in {"location_count", "total_insured_value_usd"} and not produced.locations:
            continue
        if stated != from_rows:
            findings.append(
                Finding(
                    check="total_disagrees_with_rows",
                    severity="query",
                    field=field,
                    message=(
                        f"Recorded {stated:,} but the {label} it listed come to "
                        f"{from_rows:,}."
                    ),
                )
            )
    return findings


_NONE_BOX = re.compile(r"CHK HERE IF NONE:?\s*\[X\]", re.IGNORECASE)
_PROMISED_SUMMARY = re.compile(r"SEE ATTACHED LOSS SUMMARY:?\s*\[X\]", re.IGNORECASE)


def documents_contradict_each_other(
    produced: ExtractedSubmission, packet: dict[DocumentName, str]
) -> list[Finding]:
    findings = []
    application = packet.get(DocumentName.APPLICATION, "")
    loss_runs = [
        name
        for name in (DocumentName.LOSS_RUN_A, DocumentName.LOSS_RUN_B)
        if name in packet
    ]
    answers = _answers(produced)

    declared_none = bool(_NONE_BOX.search(application))
    claims_found = len(produced.losses) > 0
    if declared_none and claims_found and not answers["loss_count_5y"].flagged:
        findings.append(
            Finding(
                check="unraised_conflict",
                severity="blocking",
                field="loss_count_5y",
                message=(
                    "The application ticks the none box while the packet's claims "
                    f"records list {len(produced.losses)}. The record carries a value "
                    "and never raises it."
                ),
                evidence=[name.value for name in loss_runs],
            )
        )

    promised = bool(_PROMISED_SUMMARY.search(application))
    if promised and not loss_runs and not answers["loss_count_5y"].flagged:
        findings.append(
            Finding(
                check="promised_document_absent",
                severity="blocking",
                field="loss_count_5y",
                message=(
                    "The application points at an attached loss summary that is not in "
                    "the packet, and the record still states a claims figure."
                ),
            )
        )
    return findings


def unsourced_defaults(produced: ExtractedSubmission) -> list[Finding]:
    findings = []
    for field, answer in _answers(produced).items():
        if answer.flagged or field not in DEFAULT_SOURCES:
            continue
        if not answer.source or not answer.source.locator.strip():
            findings.append(
                Finding(
                    check="no_locator",
                    severity="note",
                    field=field,
                    message="Named a document but not where in it, so it is slow to verify.",
                )
            )
    return findings


CHECKS = (
    citation_resolves,
    citation_is_honest,
    derived_shows_its_working,
    loss_rows_reconcile,
    totals_match_the_rows,
    documents_contradict_each_other,
    unsourced_defaults,
)


def run_all(
    produced: ExtractedSubmission, packet: dict[DocumentName, str]
) -> list[Finding]:
    findings: list[Finding] = []
    for check in CHECKS:
        try:
            result = check(produced, packet)  # type: ignore[call-arg]
        except TypeError:
            result = check(produced)  # type: ignore[call-arg]
        findings.extend(result)
    order = {"blocking": 0, "query": 1, "note": 2}
    return sorted(findings, key=lambda f: (order[f.severity], f.check))
