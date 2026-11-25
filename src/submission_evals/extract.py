from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from submission_evals.truth import DocumentName, RecommendedAction, SourceMode


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceRef(Strict):
    document: DocumentName
    mode: SourceMode
    locator: str
    derived_from: list[str]


class Extracted[T](Strict):
    kind: Literal["extracted"]
    value: T
    source: SourceRef


class Flagged(Strict):
    kind: Literal["flagged"]
    reason: str
    conflicting_sources: list[SourceRef]
    recommended_action: RecommendedAction


IntAnswer = Annotated[Extracted[int] | Flagged, Field(discriminator="kind")]
StrAnswer = Annotated[Extracted[str] | Flagged, Field(discriminator="kind")]
BoolAnswer = Annotated[Extracted[bool] | Flagged, Field(discriminator="kind")]


class LocationRow(Strict):
    loc_no: int
    street: str
    city: str
    state: str
    zip_code: str
    building_value_usd: int
    bpp_value_usd: int
    business_income_value_usd: int


class LossRow(Strict):
    carrier: str
    claim_no: str
    date_of_loss: str
    status: str
    paid_usd: int
    reserved_usd: int
    incurred_usd: int


class ExtractedSubmission(Strict):
    applicant_name: StrAnswer
    applicant_fein: StrAnswer
    applicant_entity_type: StrAnswer
    mailing_address: StrAnswer
    business_started: StrAnswer
    annual_revenue_usd: IntAnswer
    employee_count: IntAnswer
    policy_effective_date: StrAnswer
    policy_expiration_date: StrAnswer
    location_count: IntAnswer
    total_insured_value_usd: IntAnswer
    property_coinsurance_pct: IntAnswer
    property_valuation_basis: StrAnswer
    gl_each_occurrence_usd: IntAnswer
    gl_general_aggregate_usd: IntAnswer
    prior_property_carrier: StrAnswer
    loss_run_valuation_date: StrAnswer
    loss_count_5y: IntAnswer
    total_paid_5y_usd: IntAnswer
    total_incurred_5y_usd: IntAnswer
    is_update_of_prior_submission: BoolAnswer
    locations: list[LocationRow]
    losses: list[LossRow]
    packet_notes: list[str]


GRADED_FIELDS: tuple[str, ...] = (
    "applicant_name",
    "applicant_fein",
    "applicant_entity_type",
    "mailing_address",
    "business_started",
    "annual_revenue_usd",
    "employee_count",
    "policy_effective_date",
    "policy_expiration_date",
    "location_count",
    "total_insured_value_usd",
    "property_coinsurance_pct",
    "property_valuation_basis",
    "gl_each_occurrence_usd",
    "gl_general_aggregate_usd",
    "prior_property_carrier",
    "loss_run_valuation_date",
    "loss_count_5y",
    "total_paid_5y_usd",
    "total_incurred_5y_usd",
    "is_update_of_prior_submission",
)

MONEY_FIELDS: frozenset[str] = frozenset(
    {
        "annual_revenue_usd",
        "total_insured_value_usd",
        "gl_each_occurrence_usd",
        "gl_general_aggregate_usd",
        "total_paid_5y_usd",
        "total_incurred_5y_usd",
    }
)

DATE_FIELDS: frozenset[str] = frozenset(
    {
        "business_started",
        "policy_effective_date",
        "policy_expiration_date",
        "loss_run_valuation_date",
    }
)

IDENTIFIER_FIELDS: frozenset[str] = frozenset({"applicant_fein"})

COUNT_FIELDS: frozenset[str] = frozenset(
    {"employee_count", "location_count", "property_coinsurance_pct", "loss_count_5y"}
)
