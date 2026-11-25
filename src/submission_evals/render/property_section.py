from __future__ import annotations

from submission_evals.render.layout import (
    band,
    cell,
    centred,
    document,
    footer,
    money,
    row,
    rule,
    table_header,
    table_row,
    wrap,
)
from submission_evals.render.options import PacketOptions, us_date
from submission_evals.truth import Coverage, Location, Risk

_CONSTRUCTION = {
    1: "FRAME",
    2: "JOISTED MASONRY",
    3: "NON-COMBUSTIBLE",
    4: "MASONRY NON-COMBUSTIBLE",
    5: "FIRE RESISTIVE",
}

_SUBJECT_COLUMNS = (
    ("SUBJECT OF INSURANCE", 30),
    ("AMOUNT", 12),
    ("COINS%", 8),
    ("VALUATION", 11),
    ("CAUSES OF LOSS", 16),
    ("INFL GUARD%", 12),
    ("DED", 8),
)


def _subject_rows(location: Location, coverage: Coverage, options: PacketOptions) -> list[str]:
    subjects = (
        ("BUILDING", _building_value(location, options), "4"),
        ("BUSINESS PERSONAL PROPERTY", location.bpp_value_usd, "4"),
        ("BUSINESS INCOME", location.business_income_value_usd, ""),
    )
    return [
        table_row(
            (
                name,
                money(amount),
                coverage.property_coinsurance_pct,
                coverage.property_valuation_basis,
                "SPECIAL",
                guard,
                money(coverage.property_deductible_usd),
            ),
            _SUBJECT_COLUMNS,
        )
        for name, amount, guard in subjects
    ]


def _building_value(location, options: PacketOptions) -> int:
    if options.stale_location_values and location.loc_no == 1:
        return location.building_value_usd - 500_000
    return location.building_value_usd


def render(risk: Risk, options: PacketOptions) -> str:
    coverage = risk.coverage
    lines: list[str] = [
        rule(),
        centred("PROPERTY SECTION"),
        centred("(ATTACH TO COMMERCIAL INSURANCE APPLICATION)"),
        rule(),
        row(
            cell("AGENCY", options.agency, 56),
            cell("NAIC", options.target_naic, 40),
        ),
        row(cell("CARRIER", options.target_carrier, 96)),
        row(
            cell("NAMED INSURED(S)", risk.applicant.name, 60),
            cell("EFFECTIVE DATE", us_date(risk.policy.effective_date), 36),
        ),
    ]

    scheduled = risk.locations[:1] if options.premises_by_schedule else risk.locations
    for location in scheduled:
        lines.extend(
            [
                band("premises information"),
                row(
                    cell("PREMISES #", location.loc_no, 18),
                    cell("BUILDING #", 1, 18),
                    cell(
                        "STREET ADDRESS",
                        f"{location.street}, {location.city}, {location.state} {location.zip_code}",
                        60,
                    ),
                ),
                cell("BLDG DESCRIPTION", location.occupancy, 96).rstrip(),
                *table_header(_SUBJECT_COLUMNS),
                *_subject_rows(location, coverage, options),
                row(
                    cell("CONSTRUCTION TYPE", _CONSTRUCTION[location.construction_class], 46),
                    cell("DISTANCE TO HYDRANT", "180 FT", 26),
                    cell("FIRE STAT", "1.2 MI", 24),
                ),
                row(
                    cell("PROT CL", location.protection_class, 14),
                    cell("# STORIES", location.stories, 14),
                    cell("# BASM'TS", 0, 14),
                    cell("YR BUILT", location.year_built, 16),
                    cell("TOTAL AREA", money(location.square_feet), 20),
                ),
                row(
                    cell(
                        "PREMISES FIRE PROTECTION",
                        "WET SPRINKLER SYSTEM THROUGHOUT" if location.sprinklered else "NONE",
                        62,
                    ),
                    cell("% SPRNK", 100 if location.sprinklered else 0, 20),
                ),
                row(
                    cell("BURGLAR ALARM TYPE", "CENTRAL STATION", 46),
                    cell("ROOF UPDATED", min(location.year_built + 12, 2024), 26),
                ),
            ]
        )

    if options.premises_by_schedule:
        lines.extend(
            [
                band("additional premises"),
                *wrap(
                    "REMAINING INSURED LOCATIONS, VALUES, CONSTRUCTION AND PROTECTION PER THE "
                    "ATTACHED STATEMENT OF VALUES. TERMS ABOVE APPLY TO EVERY SCHEDULED "
                    "LOCATION."
                ),
            ]
        )

    lines.extend(
        [
            band("additional interest"),
            row(
                cell("INTEREST", "MORTGAGEE", 24),
                cell("NAME", "Hudson Commercial Bank", 40),
                cell("INTEREST IN ITEM", "LOCATION 1 BUILDING 1", 30),
            ),
            band("remarks"),
            "Values per the attached statement of values.",
            *footer("PROPERTY SECTION"),
        ]
    )
    return document(lines)
