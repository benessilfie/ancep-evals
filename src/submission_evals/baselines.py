from __future__ import annotations

from datetime import date
from typing import Any

from submission_evals.extract import (
    COUNT_FIELDS,
    DEFAULT_SOURCES,
    GRADED_FIELDS,
    MONEY_FIELDS,
    Answer,
    ExtractedSubmission,
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


def _primary_form(case: Case) -> DocumentName:
    for candidate in (DocumentName.APPLICATION, DocumentName.SLIP):
        if candidate in case.documents:
            return candidate
    return case.documents[0]


def _answer_source(case: Case, field: str) -> tuple[SourceRef, SourceMode]:
    expectation = case.expectation_for(field)
    fallback_document, fallback_mode = DEFAULT_SOURCES[field]
    mode = expectation.source_mode if expectation and expectation.source_mode else fallback_mode
    document = (
        expectation.source_document
        if expectation and expectation.source_document
        else fallback_document
    )
    if document not in case.documents:
        document = _primary_form(case)
        mode = SourceMode.DERIVED
    return SourceRef(document=document, locator=f"{field} on {document.value}"), mode


def extracted(case: Case, field: str, value: Any) -> Answer:
    source, mode = _answer_source(case, field)
    return Answer(
        status="extracted",
        value=str(value),
        mode=mode,
        sources=[source],
        derived_from=["statement of values rows"] if mode == SourceMode.DERIVED else [],
        reason="",
        recommended_action=RecommendedAction.NONE,
    )


def flagged(reason: str, action: RecommendedAction, sources: list[SourceRef]) -> Answer:
    return Answer(
        status="flagged",
        value="",
        mode=SourceMode.NOT_APPLICABLE,
        sources=sources,
        derived_from=[],
        reason=reason,
        recommended_action=action,
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
            source, _ = _answer_source(case, field)
            answers[field] = flagged(expectation.rationale, action, [source])
            continue
        wanted = _as_schema_value(field, expected_value(case, field))
        answers[field] = extracted(case, field, wanted)
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


def null_empty(case: Case) -> ExtractedSubmission:
    answers = {
        field: Answer(
            status="extracted",
            value=str(_zero_for(field)),
            mode=SourceMode.READ,
            sources=[SourceRef(document=_primary_form(case), locator="unknown")],
            derived_from=[],
            reason="",
            recommended_action=RecommendedAction.NONE,
        )
        for field in GRADED_FIELDS
    }
    return ExtractedSubmission(**answers, locations=[], losses=[], packet_notes=[])


def flag_everything(case: Case) -> ExtractedSubmission:
    answers = {
        field: flagged(
            "cannot determine this reliably from the packet",
            RecommendedAction.QUERY_BROKER,
            [],
        )
        for field in GRADED_FIELDS
    }
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


def plausible_liar(case: Case) -> ExtractedSubmission:
    answers: dict[str, Any] = {}
    for field in GRADED_FIELDS:
        answers[field] = Answer(
            status="extracted",
            value=str(_as_schema_value(field, expected_value(case, field))),
            mode=SourceMode.READ,
            sources=[
                SourceRef(
                    document=_primary_form(case),
                    locator="read directly from the front of the submission",
                )
            ],
            derived_from=[],
            reason="",
            recommended_action=RecommendedAction.NONE,
        )
    return ExtractedSubmission(**answers, **_rows(case), packet_notes=[])


BASELINES = {
    "oracle": oracle,
    "null_empty": null_empty,
    "flag_everything": flag_everything,
    "plausible_liar": plausible_liar,
}
