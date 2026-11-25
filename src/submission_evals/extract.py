from typing import Literal

from pydantic import BaseModel, ConfigDict

from submission_evals.truth import DocumentName, RecommendedAction, SourceMode


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceRef(Strict):
    document: DocumentName
    locator: str


class Answer(Strict):
    status: Literal["extracted", "flagged"]
    value: str
    mode: SourceMode
    sources: list[SourceRef]
    derived_from: list[str]
    reason: str
    recommended_action: RecommendedAction

    @property
    def flagged(self) -> bool:
        return self.status == "flagged"

    @property
    def source(self) -> SourceRef | None:
        return self.sources[0] if self.sources else None


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
    applicant_name: Answer
    applicant_fein: Answer
    applicant_entity_type: Answer
    mailing_address: Answer
    business_started: Answer
    annual_revenue_usd: Answer
    employee_count: Answer
    policy_effective_date: Answer
    policy_expiration_date: Answer
    location_count: Answer
    total_insured_value_usd: Answer
    property_coinsurance_pct: Answer
    property_valuation_basis: Answer
    gl_each_occurrence_usd: Answer
    gl_general_aggregate_usd: Answer
    prior_property_carrier: Answer
    loss_run_valuation_date: Answer
    loss_count_5y: Answer
    total_paid_5y_usd: Answer
    total_incurred_5y_usd: Answer
    is_update_of_prior_submission: Answer
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


DEFAULT_SOURCES: dict[str, tuple[DocumentName, SourceMode]] = {
    "applicant_name": (DocumentName.APPLICATION, SourceMode.READ),
    "applicant_fein": (DocumentName.APPLICATION, SourceMode.READ),
    "applicant_entity_type": (DocumentName.APPLICATION, SourceMode.READ),
    "mailing_address": (DocumentName.APPLICATION, SourceMode.READ),
    "business_started": (DocumentName.APPLICATION, SourceMode.READ),
    "annual_revenue_usd": (DocumentName.APPLICATION, SourceMode.READ),
    "employee_count": (DocumentName.APPLICATION, SourceMode.READ),
    "policy_effective_date": (DocumentName.APPLICATION, SourceMode.READ),
    "policy_expiration_date": (DocumentName.APPLICATION, SourceMode.READ),
    "prior_property_carrier": (DocumentName.APPLICATION, SourceMode.READ),
    "property_coinsurance_pct": (DocumentName.PROPERTY_SECTION, SourceMode.READ),
    "property_valuation_basis": (DocumentName.PROPERTY_SECTION, SourceMode.READ),
    "gl_each_occurrence_usd": (DocumentName.LIABILITY_SECTION, SourceMode.READ),
    "gl_general_aggregate_usd": (DocumentName.LIABILITY_SECTION, SourceMode.READ),
    "location_count": (DocumentName.SOV, SourceMode.DERIVED),
    "total_insured_value_usd": (DocumentName.SOV, SourceMode.DERIVED),
    "loss_run_valuation_date": (DocumentName.LOSS_RUN_A, SourceMode.READ),
    "loss_count_5y": (DocumentName.LOSS_RUN_A, SourceMode.DERIVED),
    "total_paid_5y_usd": (DocumentName.LOSS_RUN_A, SourceMode.DERIVED),
    "total_incurred_5y_usd": (DocumentName.LOSS_RUN_A, SourceMode.DERIVED),
    "is_update_of_prior_submission": (DocumentName.BROKER_EMAIL, SourceMode.DERIVED),
}

LITERAL_CHECK_EXEMPT: frozenset[str] = frozenset(
    {"mailing_address", "is_update_of_prior_submission"}
)

CODE_FIELDS: frozenset[str] = frozenset({"property_valuation_basis", "applicant_entity_type"})
