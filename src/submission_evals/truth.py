from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field


class FailureMode(StrEnum):
    STALE_THREAD = "stale_thread"
    APPLICATION_CONTRADICTS_LOSS_RUNS = "application_contradicts_loss_runs"
    DERIVED_NUMBER = "derived_number"
    LOSS_RUN_COLUMN_MISLABEL = "loss_run_column_mislabel"
    SOV_PAGE_BREAK = "sov_page_break"
    MISSING_DOCUMENT = "missing_document"
    DUPLICATE_SUBMISSION = "duplicate_submission"


class DocumentName(StrEnum):
    BROKER_EMAIL = "broker_email"
    APPLICATION = "application"
    PROPERTY_SECTION = "property_section"
    LIABILITY_SECTION = "liability_section"
    SOV = "sov"
    LOSS_RUN_A = "loss_run_a"
    LOSS_RUN_B = "loss_run_b"
    NO_LOSSES_LETTER = "no_losses_letter"


class SourceMode(StrEnum):
    READ = "read"
    DERIVED = "derived"
    NOT_APPLICABLE = "not_applicable"


class RecommendedAction(StrEnum):
    NONE = "none"
    QUERY_BROKER = "query_broker"
    REFER_TO_UNDERWRITER = "refer_to_underwriter"
    REJECT_SUBMISSION = "reject_submission"
    ASSERT_APPLICANT_MISREPRESENTED = "assert_applicant_misrepresented"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Applicant(Frozen):
    name: str
    fein: str
    entity_type: str
    street: str
    city: str
    state: str
    zip_code: str
    business_started: date


class Operations(Frozen):
    description: str
    sic_code: str
    naics_code: str
    annual_revenue_usd: int
    employee_count: int


class Policy(Frozen):
    effective_date: date
    expiration_date: date
    lines_requested: tuple[str, ...]


class Location(Frozen):
    loc_no: int
    street: str
    city: str
    state: str
    zip_code: str
    construction_class: int
    year_built: int
    stories: int
    square_feet: int
    building_value_usd: int
    bpp_value_usd: int
    business_income_value_usd: int
    occupancy: str
    sprinklered: bool
    protection_class: int

    @computed_field
    @property
    def tiv_usd(self) -> int:
        return self.building_value_usd + self.bpp_value_usd + self.business_income_value_usd


class Coverage(Frozen):
    property_coinsurance_pct: int
    property_valuation_basis: Literal["RC", "ACV"]
    property_deductible_usd: int
    gl_each_occurrence_usd: int
    gl_general_aggregate_usd: int
    gl_premium_basis: Literal["S", "P", "A"]
    gl_exposure_usd: int


class PriorCarrier(Frozen):
    carrier: str
    line: str
    policy_no: str
    period_start: date
    period_end: date
    premium_usd: int


class Loss(Frozen):
    carrier: str
    claim_no: str
    date_of_loss: date
    date_reported: date
    status: Literal["open", "closed"]
    paid_usd: int
    reserved_usd: int
    cause: str
    description: str

    @computed_field
    @property
    def incurred_usd(self) -> int:
        return self.paid_usd + self.reserved_usd


class NoLossesLetter(Frozen):
    carrier: str
    policy_no: str
    period_start: date
    period_end: date
    issued: date


class Risk(Frozen):
    applicant: Applicant
    operations: Operations
    policy: Policy
    locations: tuple[Location, ...]
    coverage: Coverage
    prior_carriers: tuple[PriorCarrier, ...]
    losses: tuple[Loss, ...]
    no_losses_letter: NoLossesLetter | None = None
    loss_run_valuation_date: date | None = None

    @computed_field
    @property
    def total_insured_value_usd(self) -> int:
        return sum(location.tiv_usd for location in self.locations)

    @computed_field
    @property
    def location_count(self) -> int:
        return len(self.locations)

    @computed_field
    @property
    def loss_count(self) -> int:
        return len(self.losses)

    @computed_field
    @property
    def total_paid_usd(self) -> int:
        return sum(loss.paid_usd for loss in self.losses)

    @computed_field
    @property
    def total_reserved_usd(self) -> int:
        return sum(loss.reserved_usd for loss in self.losses)

    @computed_field
    @property
    def total_incurred_usd(self) -> int:
        return self.total_paid_usd + self.total_reserved_usd


class SubmissionOnFile(Frozen):
    reference: str
    named_insured: str
    fein: str
    effective_date: date
    received: date
    total_insured_value_usd: int
    annual_revenue_usd: int


class Expectation(Frozen):
    field: str
    outcome: Literal["extracted", "flagged"]
    source_mode: SourceMode | None = None
    source_document: DocumentName | None = None
    allowed_actions: tuple[RecommendedAction, ...] = ()
    forbidden_actions: tuple[RecommendedAction, ...] = ()
    rationale: str
    rationale_source: str


class Case(Frozen):
    case_id: str
    title: str
    kind: Literal["control", "adversarial"]
    exercises: FailureMode | None
    risk: Risk
    corruption: str | None
    documents: tuple[DocumentName, ...]
    expectations: tuple[Expectation, ...]
    records_on_file: tuple[SubmissionOnFile, ...] = ()
    paired_with: str | None = None

    @computed_field
    @property
    def should_flag_fields(self) -> tuple[str, ...]:
        return tuple(e.field for e in self.expectations if e.outcome == "flagged")

    def expectation_for(self, field: str) -> Expectation | None:
        for expectation in self.expectations:
            if expectation.field == field:
                return expectation
        return None
