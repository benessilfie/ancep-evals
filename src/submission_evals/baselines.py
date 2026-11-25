from __future__ import annotations

from datetime import date
from typing import Any

from submission_evals.extract import (
    COUNT_FIELDS,
    GRADED_FIELDS,
    MONEY_FIELDS,
    Extracted,
    ExtractedSubmission,
    Flagged,
    LocationRow,
    LossRow,
    SourceRef,
)
from submission_evals.grade import expected_value
from submission_evals.truth import Case, DocumentName, RecommendedAction, SourceMode

INT_FIELDS = MONEY_FIELDS | COUNT_FIELDS
BOOL_FIELDS = frozenset({"is_update_of_prior_submission"})


def _as_schema_value(field: str, value: Any) -> Any:
    if field in BOOL_FIELDS:
        return bool(value)
    if field in INT_FIELDS:
        return int(value)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _zero_for(field: str) -> Any:
    if field in BOOL_FIELDS:
        return False
    if field in INT_FIELDS:
        return 0
    return ""


def _source_for(case: Case, field: str) -> SourceRef:
    expectation = case.expectation_for(field)
    mode = expectation.source_mode if expectation and expectation.source_mode else SourceMode.READ
    document = (
        expectation.source_document
        if expectation and expectation.source_document
        else DocumentName.APPLICATION
    )
    derived_from = ["statement of values rows"] if mode == SourceMode.DERIVED else []
    return SourceRef(
        document=document,
        mode=mode,
        locator=f"{field} on {document.value}",
        derived_from=derived_from,
    )


def _rows(case: Case) -> dict[str, Any]:
    return {
        "locations": [
            LocationRow(
                loc_no=location.loc_no,
                street=location.street,
                city=location.city,
                state=location.state,
                zip_code=location.zip_code,
                building_value_usd=location.building_value_usd,
                bpp_value_usd=location.bpp_value_usd,
                business_income_value_usd=location.business_income_value_usd,
            )
            for location in case.risk.locations
        ],
        "losses": [
            LossRow(
                carrier=loss.carrier,
                claim_no=loss.claim_no,
                date_of_loss=loss.date_of_loss.isoformat(),
                status=loss.status,
                paid_usd=loss.paid_usd,
                reserved_usd=loss.reserved_usd,
                incurred_usd=loss.incurred_usd,
            )
            for loss in case.risk.losses
        ],
    }


def oracle(case: Case) -> ExtractedSubmission:
    answers: dict[str, Any] = {}
    for field in GRADED_FIELDS:
        expectation = case.expectation_for(field)
        if expectation is not None and expectation.outcome == "flagged":
            action = (
                expectation.allowed_actions[0]
                if expectation.allowed_actions
                else RecommendedAction.QUERY_BROKER
            )
            answers[field] = Flagged(
                kind="flagged",
                reason=expectation.rationale,
                conflicting_sources=[_source_for(case, field)],
                recommended_action=action,
            )
            continue
        answers[field] = Extracted(
            kind="extracted",
            value=_as_schema_value(field, expected_value(case, field)),
            source=_source_for(case, field),
        )
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


def null_empty(case: Case) -> ExtractedSubmission:
    answers = {
        field: Extracted(
            kind="extracted",
            value=_zero_for(field),
            source=SourceRef(
                document=DocumentName.APPLICATION,
                mode=SourceMode.READ,
                locator="unknown",
                derived_from=[],
            ),
        )
        for field in GRADED_FIELDS
    }
    return ExtractedSubmission(**answers, locations=[], losses=[], packet_notes=[])


def flag_everything(case: Case) -> ExtractedSubmission:
    answers = {
        field: Flagged(
            kind="flagged",
            reason="cannot determine this reliably from the packet",
            conflicting_sources=[],
            recommended_action=RecommendedAction.QUERY_BROKER,
        )
        for field in GRADED_FIELDS
    }
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


def plausible_liar(case: Case) -> ExtractedSubmission:
    answers: dict[str, Any] = {}
    for field in GRADED_FIELDS:
        answers[field] = Extracted(
            kind="extracted",
            value=_as_schema_value(field, expected_value(case, field)),
            source=SourceRef(
                document=DocumentName.APPLICATION,
                mode=SourceMode.READ,
                locator="read directly from the application form",
                derived_from=[],
            ),
        )
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


BASELINES = {
    "oracle": oracle,
    "null_empty": null_empty,
    "flag_everything": flag_everything,
    "plausible_liar": plausible_liar,
}
