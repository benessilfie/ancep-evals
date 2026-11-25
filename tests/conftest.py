from datetime import date

import pytest

from submission_evals.truth import (
    Applicant,
    Case,
    Coverage,
    DocumentName,
    Expectation,
    FailureMode,
    Location,
    Loss,
    Operations,
    Policy,
    PriorCarrier,
    RecommendedAction,
    Risk,
    SourceMode,
)

_SITES = (
    (1, "18 Washington Street", "Hoboken", "07030", 1962, 4200, 1_200_000, 400_000, 250_000),
    (2, "7 Palisade Avenue", "Jersey City", "07306", 1998, 2100, 650_000, 180_000, 120_000),
    (3, "214 Central Avenue", "Jersey City", "07307", 2004, 5600, 1_500_000, 250_000, 150_000),
    (4, "41 Bergenline Avenue", "Union City", "07087", 2011, 3100, 780_000, 220_000, 140_000),
    (5, "3 Kennedy Boulevard", "Bayonne", "07002", 1988, 4800, 1_100_000, 300_000, 180_000),
    (6, "90 Port Street", "Newark", "07114", 2015, 1800, 740_000, 150_000, 90_000),
)

_ALL_DOCUMENTS = (
    DocumentName.BROKER_EMAIL,
    DocumentName.APPLICATION,
    DocumentName.PROPERTY_SECTION,
    DocumentName.SOV,
    DocumentName.LOSS_RUN_A,
    DocumentName.LOSS_RUN_B,
)


def build_risk() -> Risk:
    return Risk(
        applicant=Applicant(
            name="Halsey Street Bakery LLC",
            fein="47-3918266",
            entity_type="LLC",
            street="18 Washington Street",
            city="Hoboken",
            state="NJ",
            zip_code="07030",
            business_started=date(2009, 4, 6),
        ),
        operations=Operations(
            description="Retail bakery chain, six outlets, on-site baking and a delivery fleet",
            sic_code="5461",
            naics_code="311811",
            annual_revenue_usd=9_400_000,
            employee_count=40,
        ),
        policy=Policy(
            effective_date=date(2027, 1, 1),
            expiration_date=date(2028, 1, 1),
            lines_requested=("Property", "Commercial General Liability"),
        ),
        locations=tuple(
            Location(
                loc_no=loc_no,
                street=street,
                city=city,
                state="NJ",
                zip_code=zip_code,
                construction_class=2,
                year_built=year_built,
                stories=1,
                square_feet=square_feet,
                building_value_usd=building,
                bpp_value_usd=bpp,
                business_income_value_usd=bi,
                occupancy="Bakery, retail with on-site baking",
                sprinklered=True,
                protection_class=4,
            )
            for loc_no, street, city, zip_code, year_built, square_feet, building, bpp, bi in _SITES
        ),
        coverage=Coverage(
            property_coinsurance_pct=90,
            property_valuation_basis="RC",
            property_deductible_usd=10_000,
            gl_each_occurrence_usd=1_000_000,
            gl_general_aggregate_usd=2_000_000,
            gl_premium_basis="S",
            gl_exposure_usd=9_400_000,
        ),
        prior_carriers=(
            PriorCarrier(
                carrier="Meridian Mutual",
                line="Property",
                policy_no="MM-PR-4480912",
                period_start=date(2026, 1, 1),
                period_end=date(2027, 1, 1),
                premium_usd=41_200,
            ),
            PriorCarrier(
                carrier="Callaghan Indemnity",
                line="General Liability",
                policy_no="CI-GL-77301",
                period_start=date(2026, 1, 1),
                period_end=date(2027, 1, 1),
                premium_usd=18_600,
            ),
        ),
        losses=(
            Loss(
                carrier="Meridian Mutual",
                claim_no="884213",
                date_of_loss=date(2024, 1, 14),
                date_reported=date(2024, 1, 16),
                status="closed",
                paid_usd=12_000,
                reserved_usd=0,
                cause="Water damage",
                description="Burst supply line in the Hoboken prep kitchen",
            ),
            Loss(
                carrier="Callaghan Indemnity",
                claim_no="901887",
                date_of_loss=date(2025, 3, 3),
                date_reported=date(2025, 3, 11),
                status="open",
                paid_usd=4_000,
                reserved_usd=26_000,
                cause="Bodily injury",
                description="Customer slipped on a wet floor at the Central Avenue outlet",
            ),
        ),
        loss_run_valuation_date=date(2026, 11, 30),
    )


def _rationale(text: str) -> dict[str, str]:
    return {"rationale": text, "rationale_source": "https://example.invalid/fixture"}


@pytest.fixture
def risk() -> Risk:
    return build_risk()


@pytest.fixture
def control_case(risk: Risk) -> Case:
    return Case(
        case_id="fixture-control",
        title="Total stated in the broker email",
        kind="control",
        exercises=None,
        risk=risk,
        corruption=None,
        documents=_ALL_DOCUMENTS,
        expectations=(
            Expectation(
                field="total_insured_value_usd",
                outcome="extracted",
                source_mode=SourceMode.READ,
                source_document=DocumentName.BROKER_EMAIL,
                **_rationale("The broker states the total in the covering email."),
            ),
        ),
    )


@pytest.fixture
def derived_case(risk: Risk) -> Case:
    return Case(
        case_id="fixture-derived",
        title="Total appears nowhere in the packet",
        kind="adversarial",
        exercises=FailureMode.DERIVED_NUMBER,
        risk=risk,
        corruption="strip_total_insured_value",
        documents=_ALL_DOCUMENTS,
        expectations=(
            Expectation(
                field="total_insured_value_usd",
                outcome="extracted",
                source_mode=SourceMode.DERIVED,
                source_document=DocumentName.SOV,
                **_rationale("No ACORD property form carries a total; it must be summed."),
            ),
        ),
    )


@pytest.fixture
def conflict_case(risk: Risk) -> Case:
    return Case(
        case_id="fixture-conflict",
        title="Application declares no losses while loss runs show two",
        kind="adversarial",
        exercises=FailureMode.APPLICATION_CONTRADICTS_LOSS_RUNS,
        risk=risk,
        corruption="tick_no_losses_box",
        documents=_ALL_DOCUMENTS,
        expectations=(
            Expectation(
                field="loss_count_5y",
                outcome="flagged",
                allowed_actions=(
                    RecommendedAction.QUERY_BROKER,
                    RecommendedAction.REFER_TO_UNDERWRITER,
                ),
                forbidden_actions=(RecommendedAction.ASSERT_APPLICANT_MISREPRESENTED,),
                **_rationale("A conflicting value becomes a request to the broker, never a guess."),
            ),
        ),
    )
