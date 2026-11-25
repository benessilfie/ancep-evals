from __future__ import annotations

from datetime import date

from submission_evals.generate import CaseSpec
from submission_evals.manifest import documents_for
from submission_evals.render.options import PacketOptions
from submission_evals.truth import (
    Applicant,
    Case,
    Coverage,
    DocumentName,
    Expectation,
    FailureMode,
    Location,
    Loss,
    NoLossesLetter,
    Operations,
    Policy,
    PriorCarrier,
    RecommendedAction,
    Risk,
    SourceMode,
)

SOURCE_ACORD_140 = "https://acicompanies.com/PrivateSite/Pdfs/Forms/Acord_140_201403.pdf"
SOURCE_ACORD_125 = "https://easternunderwritingmanagers.com/wp-content/uploads/Acord-125.pdf"
SOURCE_LOSS_RUNS = "https://www.menloinsurance.com/library/guides/how-to-read-loss-runs"
SOURCE_LOSS_RUN_FORMATS = "https://sortspoke.com/blog/what-is-a-loss-run-report"
SOURCE_INCURRED = (
    "https://www.milliman.com/en/insight/a-beginners-guide-to-the-casualty-actuarial-language"
)
SOURCE_EXTRACTION = "https://www.docsumo.com/blog/loss-run-data-extraction"
SOURCE_BROKER_QUERY = (
    "https://insops.com/blogs/why-broker-submissions-fail-on-first-receipt-and-how-to-fix-it"
)
SOURCE_CLEARANCE = "https://help.vertafore.com/AIM/content/insured_clearance_search.htm"
SOURCE_SOV = (
    "https://www.independentagent.com/vu_resource/"
    "helping-your-clients-maintain-accurate-statements-of-value/"
)

_SITES = (
    ("18 Washington Street", "Hoboken", "07030", 1962, 4200, 1_200_000, 400_000, 250_000),
    ("7 Palisade Avenue", "Jersey City", "07306", 1998, 2100, 650_000, 180_000, 120_000),
    ("214 Central Avenue", "Jersey City", "07307", 2004, 5600, 1_500_000, 250_000, 150_000),
    ("41 Bergenline Avenue", "Union City", "07087", 2011, 3100, 780_000, 220_000, 140_000),
    ("3 Kennedy Boulevard", "Bayonne", "07002", 1988, 4800, 1_100_000, 300_000, 180_000),
    ("90 Port Street", "Newark", "07114", 2015, 1800, 740_000, 150_000, 90_000),
    ("52 Observer Highway", "Hoboken", "07030", 1975, 2600, 820_000, 210_000, 130_000),
    ("8 Journal Square", "Jersey City", "07306", 1969, 3400, 960_000, 240_000, 150_000),
    ("301 Broadway", "Bayonne", "07002", 1992, 2200, 610_000, 170_000, 110_000),
    ("77 Ferry Street", "Newark", "07105", 2001, 4100, 1_040_000, 280_000, 160_000),
    ("14 Summit Avenue", "Union City", "07087", 1983, 1900, 580_000, 160_000, 100_000),
    ("190 Grand Street", "Jersey City", "07302", 2008, 5200, 1_320_000, 330_000, 190_000),
    ("6 Willow Terrace", "Hoboken", "07030", 1958, 1600, 520_000, 140_000, 90_000),
    ("45 Raymond Boulevard", "Newark", "07102", 2013, 3700, 1_010_000, 260_000, 150_000),
)


def _locations(count: int) -> tuple[Location, ...]:
    return tuple(
        Location(
            loc_no=index + 1,
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
        for index, (street, city, zip_code, year_built, square_feet, building, bpp, bi) in (
            enumerate(_SITES[:count])
        )
    )


_PRIOR_CARRIERS = (
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
)

_LOSSES = (
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
)


def build_risk(
    location_count: int = 6,
    *,
    with_losses: bool = True,
    with_letter: bool = False,
    annual_revenue_usd: int = 9_400_000,
) -> Risk:
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
            description=(
                "Retail bakery chain, on-site baking at every outlet and a delivery fleet"
            ),
            sic_code="5461",
            naics_code="311811",
            annual_revenue_usd=annual_revenue_usd,
            employee_count=40,
        ),
        policy=Policy(
            effective_date=date(2027, 1, 1),
            expiration_date=date(2028, 1, 1),
            lines_requested=("Property", "Commercial General Liability"),
        ),
        locations=_locations(location_count),
        coverage=Coverage(
            property_coinsurance_pct=90,
            property_valuation_basis="RC",
            property_deductible_usd=10_000,
            gl_each_occurrence_usd=1_000_000,
            gl_general_aggregate_usd=2_000_000,
            gl_premium_basis="S",
            gl_exposure_usd=annual_revenue_usd,
        ),
        prior_carriers=_PRIOR_CARRIERS,
        losses=_LOSSES if with_losses else (),
        no_losses_letter=(
            NoLossesLetter(
                carrier="Meridian Mutual",
                policy_no="MM-PR-4480912",
                period_start=date(2022, 1, 1),
                period_end=date(2027, 1, 1),
                issued=date(2026, 11, 30),
            )
            if with_letter
            else None
        ),
        loss_run_valuation_date=date(2026, 11, 30),
    )


def _spec(
    case_id: str,
    title: str,
    kind: str,
    exercises: FailureMode | None,
    risk: Risk,
    options: PacketOptions,
    expectations: tuple[Expectation, ...],
    corruption: str | None = None,
    paired_with: str | None = None,
) -> CaseSpec:
    return CaseSpec(
        case=Case(
            case_id=case_id,
            title=title,
            kind=kind,
            exercises=exercises,
            risk=risk,
            corruption=corruption,
            documents=documents_for(risk, options),
            expectations=expectations,
            paired_with=paired_with,
        ),
        options=options,
    )


def _total_read_from_email() -> Expectation:
    return Expectation(
        field="total_insured_value_usd",
        outcome="extracted",
        source_mode=SourceMode.READ,
        source_document=DocumentName.BROKER_EMAIL,
        rationale=(
            "The broker states the total sum insured in the covering email, so the figure "
            "was read and not computed."
        ),
        rationale_source=SOURCE_ACORD_140,
    )


def all_specs() -> list[CaseSpec]:
    base = build_risk(6)
    single = build_risk(1)
    wide = build_risk(14)
    clean = build_risk(6, with_losses=False, with_letter=True)
    resent = build_risk(6, annual_revenue_usd=9_950_000)

    return [
        _spec(
            "01-clean-single-location",
            "One location, every figure stated where you would expect it",
            "control",
            None,
            single,
            PacketOptions(),
            (_total_read_from_email(),),
        ),
        _spec(
            "02-clean-total-stated",
            "Six locations and the broker states the total in the email",
            "control",
            None,
            base,
            PacketOptions(),
            (_total_read_from_email(),),
            paired_with="06-derived-total",
        ),
        _spec(
            "03-clean-no-losses-letter",
            "Genuinely no losses, with the carrier's no losses letter attached",
            "control",
            None,
            clean,
            PacketOptions(include_loss_runs=False, include_no_losses_letter=True),
            (
                Expectation(
                    field="loss_count_5y",
                    outcome="extracted",
                    source_mode=SourceMode.READ,
                    source_document=DocumentName.NO_LOSSES_LETTER,
                    rationale=(
                        "Where there are genuinely no claims the carrier issues a no losses "
                        "letter, so zero is an answer with a document behind it and not a gap "
                        "in the packet."
                    ),
                    rationale_source=SOURCE_LOSS_RUNS,
                ),
                Expectation(
                    field="loss_run_valuation_date",
                    outcome="extracted",
                    source_mode=SourceMode.READ,
                    source_document=DocumentName.NO_LOSSES_LETTER,
                    rationale="The letter carries the date the claim records were read.",
                    rationale_source=SOURCE_LOSS_RUNS,
                ),
            ),
            paired_with="09-missing-loss-runs",
        ),
        _spec(
            "04-stale-thread",
            "The total is corrected three messages down a forwarded chain",
            "adversarial",
            FailureMode.STALE_THREAD,
            base,
            PacketOptions(stale_total_in_email=7_900_000),
            (
                Expectation(
                    field="total_insured_value_usd",
                    outcome="extracted",
                    source_mode=SourceMode.READ,
                    source_document=DocumentName.BROKER_EMAIL,
                    rationale=(
                        "The newest message in a forwarded chain is at the top but the newest "
                        "fact is further down, and the corrected total is the one that binds."
                    ),
                    rationale_source=SOURCE_SOV,
                ),
            ),
            corruption="stale_total_at_top_of_thread",
        ),
        _spec(
            "05-application-contradicts-loss-runs",
            "The none box is ticked while the attached loss runs show two claims",
            "adversarial",
            FailureMode.APPLICATION_CONTRADICTS_LOSS_RUNS,
            base,
            PacketOptions(tick_no_losses_box=True),
            (
                Expectation(
                    field="loss_count_5y",
                    outcome="flagged",
                    allowed_actions=(
                        RecommendedAction.QUERY_BROKER,
                        RecommendedAction.REFER_TO_UNDERWRITER,
                    ),
                    forbidden_actions=(RecommendedAction.ASSERT_APPLICANT_MISREPRESENTED,),
                    rationale=(
                        "A conflicting value becomes a request to the broker and never a guess. "
                        "The applicant may have answered honestly about claims they knew of, so "
                        "asserting misrepresentation is also wrong."
                    ),
                    rationale_source=SOURCE_BROKER_QUERY,
                ),
            ),
            corruption="tick_no_losses_box",
        ),
        _spec(
            "06-derived-total",
            "Case 02 with the total removed from every document",
            "adversarial",
            FailureMode.DERIVED_NUMBER,
            base,
            PacketOptions(state_total_in_email=False),
            (
                Expectation(
                    field="total_insured_value_usd",
                    outcome="extracted",
                    source_mode=SourceMode.DERIVED,
                    source_document=DocumentName.SOV,
                    rationale=(
                        "The property section carries amounts per subject of insurance per "
                        "building and has no total field at all, so a total can only be summed "
                        "and must be recorded as derived."
                    ),
                    rationale_source=SOURCE_ACORD_140,
                ),
            ),
            corruption="strip_total_from_email",
            paired_with="02-clean-total-stated",
        ),
        _spec(
            "07-loss-run-column-mislabel",
            "One carrier's paid column actually holds the incurred figure",
            "adversarial",
            FailureMode.LOSS_RUN_COLUMN_MISLABEL,
            base,
            PacketOptions(mislabel_loss_run_b_columns=True),
            (
                Expectation(
                    field="total_paid_5y_usd",
                    outcome="flagged",
                    allowed_actions=(
                        RecommendedAction.QUERY_BROKER,
                        RecommendedAction.REFER_TO_UNDERWRITER,
                    ),
                    rationale=(
                        "Paid plus reserved equals incurred on every row, so a row where it does "
                        "not add up means a column is mislabelled and the paid figure cannot be "
                        "trusted. Carriers label these columns differently."
                    ),
                    rationale_source=SOURCE_INCURRED,
                ),
            ),
            corruption="swap_paid_for_incurred",
        ),
        _spec(
            "08-sov-page-break",
            "The last location splits across a page break in the statement of values",
            "adversarial",
            FailureMode.SOV_PAGE_BREAK,
            wide,
            PacketOptions(sov_as_paged_text=True, sov_page_break_after=13),
            (
                Expectation(
                    field="location_count",
                    outcome="extracted",
                    source_mode=SourceMode.DERIVED,
                    source_document=DocumentName.SOV,
                    rationale=(
                        "Column headers appear on the first page only and rows continue "
                        "underneath, so a split row is read as missing or counted twice."
                    ),
                    rationale_source=SOURCE_EXTRACTION,
                ),
            ),
            corruption="split_last_location_across_pages",
        ),
        _spec(
            "09-missing-loss-runs",
            "No loss runs attached and no letter either",
            "adversarial",
            FailureMode.MISSING_DOCUMENT,
            base,
            PacketOptions(include_loss_runs=False),
            (
                Expectation(
                    field="loss_count_5y",
                    outcome="flagged",
                    allowed_actions=(
                        RecommendedAction.QUERY_BROKER,
                        RecommendedAction.REFER_TO_UNDERWRITER,
                    ),
                    rationale=(
                        "An absent loss run is an incomplete packet, not a nil claims history. "
                        "The carrier issues a no losses letter when there is genuinely nothing, "
                        "so silence means go back to the broker."
                    ),
                    rationale_source=SOURCE_LOSS_RUNS,
                ),
                Expectation(
                    field="loss_run_valuation_date",
                    outcome="flagged",
                    allowed_actions=(
                        RecommendedAction.QUERY_BROKER,
                        RecommendedAction.REFER_TO_UNDERWRITER,
                    ),
                    rationale="There is no loss run, so there is no valuation date to read.",
                    rationale_source=SOURCE_LOSS_RUN_FORMATS,
                ),
            ),
            corruption="drop_loss_runs",
        ),
        _spec(
            "10-duplicate-submission",
            "The same risk resent a week later with the revenue changed",
            "adversarial",
            FailureMode.DUPLICATE_SUBMISSION,
            resent,
            PacketOptions(
                submitted_on=date(2026, 12, 14),
                resend_note=(
                    "Resending this one, the revenue figure moved after their year end so "
                    "please use this version."
                ),
            ),
            (
                Expectation(
                    field="is_update_of_prior_submission",
                    outcome="extracted",
                    source_mode=SourceMode.DERIVED,
                    source_document=DocumentName.BROKER_EMAIL,
                    rationale=(
                        "Clearance checks whether the same risk is already in the system before "
                        "a submission is worked, because opening a second record on one risk "
                        "distorts the pipeline and the broker of record position."
                    ),
                    rationale_source=SOURCE_CLEARANCE,
                ),
            ),
            corruption="resend_with_changed_revenue",
            paired_with="02-clean-total-stated",
        ),
    ]


def spec_by_id(case_id: str) -> CaseSpec:
    for spec in all_specs():
        if spec.case.case_id == case_id:
            return spec
    raise KeyError(case_id)
