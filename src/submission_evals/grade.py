from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel

from submission_evals.extract import (
    DATE_FIELDS,
    GRADED_FIELDS,
    IDENTIFIER_FIELDS,
    MONEY_FIELDS,
    Extracted,
    ExtractedSubmission,
    Flagged,
    SourceRef,
)
from submission_evals.truth import Case, DocumentName, SourceMode

FlagDecision = Literal["correctly_flagged", "correctly_not_flagged", "missed_flag", "spurious_flag"]

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%d %B %Y", "%b %d, %Y")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")
_ENTITY_NOISE = re.compile(r"\b(inc|llc|ltd|corp|co|company|incorporated|limited)\b")


def normalise_text(value: Any) -> str:
    return _WHITESPACE.sub(" ", str(value).strip().casefold())


def normalise_identifier(value: Any) -> str:
    return _NON_ALNUM.sub("", str(value).casefold())


def normalise_name(value: Any) -> str:
    stripped = _ENTITY_NOISE.sub("", normalise_text(value))
    return _NON_ALNUM.sub("", stripped)


def normalise_date(value: Any) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value).strip().replace(".", "")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalise_money(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    raw = re.sub(r"[^0-9.\-]", "", str(value))
    if not raw:
        return None
    try:
        return round(float(raw))
    except ValueError:
        return None


def expected_value(case: Case, field: str) -> Any:
    risk = case.risk
    table: dict[str, Any] = {
        "applicant_name": risk.applicant.name,
        "applicant_fein": risk.applicant.fein,
        "applicant_entity_type": risk.applicant.entity_type,
        "mailing_address": (
            f"{risk.applicant.street}, {risk.applicant.city}, "
            f"{risk.applicant.state} {risk.applicant.zip_code}"
        ),
        "business_started": risk.applicant.business_started,
        "annual_revenue_usd": risk.operations.annual_revenue_usd,
        "employee_count": risk.operations.employee_count,
        "policy_effective_date": risk.policy.effective_date,
        "policy_expiration_date": risk.policy.expiration_date,
        "location_count": risk.location_count,
        "total_insured_value_usd": risk.total_insured_value_usd,
        "property_coinsurance_pct": risk.coverage.property_coinsurance_pct,
        "property_valuation_basis": risk.coverage.property_valuation_basis,
        "gl_each_occurrence_usd": risk.coverage.gl_each_occurrence_usd,
        "gl_general_aggregate_usd": risk.coverage.gl_general_aggregate_usd,
        "prior_property_carrier": next(
            (p.carrier for p in risk.prior_carriers if p.line.casefold() == "property"), ""
        ),
        "loss_run_valuation_date": risk.loss_run_valuation_date,
        "loss_count_5y": risk.loss_count,
        "total_paid_5y_usd": risk.total_paid_usd,
        "total_incurred_5y_usd": risk.total_incurred_usd,
        "is_update_of_prior_submission": case.exercises is not None
        and case.exercises.value == "duplicate_submission",
    }
    return table[field]


def values_match(field: str, expected: Any, actual: Any) -> bool:
    if field in MONEY_FIELDS:
        return normalise_money(actual) == normalise_money(expected)
    if field in DATE_FIELDS:
        normalised_actual = normalise_date(actual)
        normalised_expected = normalise_date(expected)
        return normalised_actual is not None and normalised_actual == normalised_expected
    if field in IDENTIFIER_FIELDS:
        return normalise_identifier(actual) == normalise_identifier(expected)
    if field == "is_update_of_prior_submission":
        return bool(actual) is bool(expected)
    if field == "mailing_address":
        haystack = normalise_identifier(actual)
        return all(
            normalise_identifier(part) in haystack
            for part in (
                expected.split(",")[0].split()[0],
                expected.split()[-1],
                expected.split(",")[-1].split()[0],
            )
        )
    if field == "applicant_name":
        return normalise_name(actual) == normalise_name(expected)
    if isinstance(expected, int):
        return normalise_money(actual) == expected
    return normalise_text(actual) == normalise_text(expected)


def renderings(field: str, value: Any) -> list[str]:
    if field in MONEY_FIELDS or isinstance(value, int):
        number = normalise_money(value)
        if number is None:
            return [str(value)]
        return [f"{number:,}", str(number), f"${number:,}", f"{number:,.2f}"]
    if field in DATE_FIELDS:
        iso = normalise_date(value)
        if iso is None:
            return [str(value)]
        parsed = datetime.strptime(iso, "%Y-%m-%d").date()
        return [iso, parsed.strftime("%m/%d/%Y"), parsed.strftime("%B %d, %Y")]
    return [str(value)]


class ProvenanceVerdict(BaseModel):
    structural: bool
    resolvable: bool
    semantic: bool
    detail: str

    @property
    def ok(self) -> bool:
        return self.structural and self.resolvable and self.semantic


def grade_provenance(
    case: Case,
    field: str,
    source: SourceRef,
    value: Any,
    packet_text: dict[DocumentName, str] | None,
) -> ProvenanceVerdict:
    structural = bool(source.locator.strip()) and (
        source.mode != SourceMode.DERIVED or bool(source.derived_from)
    )
    if not structural:
        return ProvenanceVerdict(
            structural=False,
            resolvable=False,
            semantic=False,
            detail="source ref malformed or derived without inputs",
        )

    resolvable = source.document in case.documents
    if not resolvable:
        return ProvenanceVerdict(
            structural=True,
            resolvable=False,
            semantic=False,
            detail=f"cited {source.document.value}, not in this packet",
        )

    expectation = case.expectation_for(field)
    if (
        expectation is not None
        and expectation.source_mode is not None
        and source.mode != expectation.source_mode
    ):
        return ProvenanceVerdict(
            structural=True,
            resolvable=True,
            semantic=False,
            detail=(
                f"claimed mode {source.mode.value}, correct mode is {expectation.source_mode.value}"
            ),
        )
    if (
        expectation is not None
        and expectation.source_document is not None
        and source.document != expectation.source_document
    ):
        return ProvenanceVerdict(
            structural=True,
            resolvable=True,
            semantic=False,
            detail=(
                f"cited {source.document.value}, "
                f"correct document is {expectation.source_document.value}"
            ),
        )

    if packet_text is not None and source.mode == SourceMode.READ:
        body = packet_text.get(source.document, "")
        if not any(form in body for form in renderings(field, value)):
            return ProvenanceVerdict(
                structural=True,
                resolvable=True,
                semantic=False,
                detail=f"claimed read from {source.document.value} but value is not in it",
            )

    return ProvenanceVerdict(structural=True, resolvable=True, semantic=True, detail="ok")


class FieldVerdict(BaseModel):
    field: str
    declared: bool
    expected_outcome: Literal["extracted", "flagged"]
    actual_outcome: Literal["extracted", "flagged"]
    flag_decision: FlagDecision
    value_correct: bool | None
    provenance: ProvenanceVerdict | None
    action_ok: bool | None
    detail: str


def grade_field(
    case: Case,
    field: str,
    answer: Extracted[Any] | Flagged,
    packet_text: dict[DocumentName, str] | None,
) -> FieldVerdict:
    expectation = case.expectation_for(field)
    expected_outcome = expectation.outcome if expectation else "extracted"
    actual_outcome = "flagged" if isinstance(answer, Flagged) else "extracted"

    if expected_outcome == "flagged":
        decision: FlagDecision = (
            "correctly_flagged" if actual_outcome == "flagged" else "missed_flag"
        )
    else:
        decision = "spurious_flag" if actual_outcome == "flagged" else "correctly_not_flagged"

    if isinstance(answer, Flagged):
        action_ok: bool | None = None
        detail = f"flagged: {answer.reason[:120]}"
        if expectation is not None:
            forbidden = expectation.forbidden_actions
            if forbidden and answer.recommended_action in forbidden:
                action_ok = False
                detail = f"flagged but recommended {answer.recommended_action.value}"
            elif expectation.allowed_actions:
                action_ok = answer.recommended_action in expectation.allowed_actions
                if not action_ok:
                    detail = f"flagged but recommended {answer.recommended_action.value}"
        return FieldVerdict(
            field=field,
            declared=expectation is not None,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            flag_decision=decision,
            value_correct=None,
            provenance=None,
            action_ok=action_ok,
            detail=detail,
        )

    wanted = expected_value(case, field)
    value_correct = values_match(field, wanted, answer.value)
    provenance = grade_provenance(case, field, answer.source, answer.value, packet_text)
    return FieldVerdict(
        field=field,
        declared=expectation is not None,
        expected_outcome=expected_outcome,
        actual_outcome=actual_outcome,
        flag_decision=decision,
        value_correct=value_correct,
        provenance=provenance,
        action_ok=None,
        detail=(
            "ok"
            if value_correct and provenance.ok
            else f"value={answer.value!r} wanted={wanted!r}; {provenance.detail}"
        ),
    )


class CaseVerdict(BaseModel):
    case_id: str
    kind: Literal["control", "adversarial"]
    fields: list[FieldVerdict]
    loss_rows_arithmetic_consistent: bool
    location_rows_correct: bool
    loss_rows_correct: bool
    case_passed: bool

    @property
    def value_score(self) -> float:
        scored = [f for f in self.fields if f.value_correct is not None]
        return sum(f.value_correct for f in scored) / len(scored) if scored else 0.0

    @property
    def provenance_score(self) -> float:
        scored = [f for f in self.fields if f.provenance is not None]
        return sum(f.provenance.ok for f in scored) / len(scored) if scored else 0.0

    @property
    def flag_counts(self) -> dict[FlagDecision, int]:
        counts: dict[FlagDecision, int] = {
            "correctly_flagged": 0,
            "correctly_not_flagged": 0,
            "missed_flag": 0,
            "spurious_flag": 0,
        }
        for verdict in self.fields:
            counts[verdict.flag_decision] += 1
        return counts


def grade(
    case: Case,
    produced: ExtractedSubmission,
    packet_text: dict[DocumentName, str] | None = None,
) -> CaseVerdict:
    verdicts = [
        grade_field(case, field, getattr(produced, field), packet_text) for field in GRADED_FIELDS
    ]

    arithmetic = all(row.paid_usd + row.reserved_usd == row.incurred_usd for row in produced.losses)
    locations_correct = len(produced.locations) == case.risk.location_count and {
        row.loc_no for row in produced.locations
    } == {location.loc_no for location in case.risk.locations}
    losses_correct = len(produced.losses) == case.risk.loss_count

    declared = [v for v in verdicts if v.declared]
    expectations_met = all(
        v.flag_decision in ("correctly_flagged", "correctly_not_flagged")
        and (v.value_correct is not False)
        and (v.provenance is None or v.provenance.ok)
        and (v.action_ok is not False)
        for v in declared
    )
    no_blanket_refusal = not any(v.flag_decision == "spurious_flag" for v in verdicts)

    return CaseVerdict(
        case_id=case.case_id,
        kind=case.kind,
        fields=verdicts,
        loss_rows_arithmetic_consistent=arithmetic,
        location_rows_correct=locations_correct,
        loss_rows_correct=losses_correct,
        case_passed=expectations_met and no_blanket_refusal,
    )
