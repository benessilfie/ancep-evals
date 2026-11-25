from __future__ import annotations

from submission_evals.render.layout import (
    band,
    box,
    cell,
    centred,
    document,
    footer,
    money,
    row,
    rule,
    table_header,
    table_row,
    ticked,
    wrap,
)
from submission_evals.render.options import PacketOptions, us_date
from submission_evals.truth import Risk

_BASIS_LEGEND = {
    "S": "GROSS SALES",
    "P": "PAYROLL",
    "A": "AREA",
}

_HAZARD_COLUMNS = (
    ("LOC", 5),
    ("CLASSIFICATION", 42),
    ("CLASS CODE", 12),
    ("PREMIUM BASIS", 15),
    ("EXPOSURE", 14),
)

_LIMIT_ROWS = (
    "GENERAL AGGREGATE",
    "PRODUCTS AND COMPLETED OPERATIONS AGGREGATE",
    "PERSONAL AND ADVERTISING INJURY",
    "EACH OCCURRENCE",
    "DAMAGE TO RENTED PREMISES",
    "MEDICAL EXPENSE",
)

_GL_QUESTIONS = (
    ("DOES THE APPLICANT USE SUBCONTRACTORS?", False),
    ("ARE CERTIFICATES OF INSURANCE OBTAINED FROM SUBCONTRACTORS?", False),
    ("ANY WORK PERFORMED AT HEIGHT OR BELOW GROUND?", False),
    ("ANY PRODUCTS SOLD UNDER THE APPLICANT'S OWN LABEL?", True),
    ("ANY DELIVERY BY OWN VEHICLES?", True),
    ("ANY ALCOHOL SOLD OR SERVED?", False),
)


def render(risk: Risk, options: PacketOptions) -> str:
    coverage = risk.coverage
    limits = {
        "GENERAL AGGREGATE": coverage.gl_general_aggregate_usd,
        "PRODUCTS AND COMPLETED OPERATIONS AGGREGATE": coverage.gl_general_aggregate_usd,
        "PERSONAL AND ADVERTISING INJURY": coverage.gl_each_occurrence_usd,
        "EACH OCCURRENCE": coverage.gl_each_occurrence_usd,
        "DAMAGE TO RENTED PREMISES": 100_000,
        "MEDICAL EXPENSE": 10_000,
    }
    lines: list[str] = [
        rule(),
        centred("COMMERCIAL GENERAL LIABILITY SECTION"),
        centred("(ATTACH TO COMMERCIAL INSURANCE APPLICATION)"),
        rule(),
        row(
            cell("AGENCY", options.agency, 48),
            cell("CARRIER", risk.prior_carriers[1].carrier, 30),
            cell("NAIC", "19201", 18),
        ),
        row(
            cell("NAMED INSURED(S)", risk.applicant.name, 56),
            cell("EFFECTIVE DATE", us_date(risk.policy.effective_date), 40),
        ),
        band("coverage"),
        row(
            ticked(True, "COMMERCIAL GENERAL LIABILITY", 48),
            ticked(True, "OCCURRENCE", 22),
            ticked(False, "CLAIMS MADE", 22),
        ),
        cell("RETRO DATE", "", 40),
        band("limits of insurance"),
    ]
    for name in _LIMIT_ROWS:
        lines.append(f"{name.ljust(60)}{money(limits[name]).rjust(14)}")

    lines.extend(
        [
            band("deductibles"),
            row(
                cell("PROPERTY DAMAGE DEDUCTIBLE", money(1_000), 48),
                cell("PER", "CLAIM", 24),
            ),
            band("schedule of hazards"),
            *table_header(_HAZARD_COLUMNS),
        ]
    )
    exposure_per_site = coverage.gl_exposure_usd // max(risk.location_count, 1)
    for location in risk.locations:
        lines.append(
            table_row(
                (
                    location.loc_no,
                    "BAKERIES - RETAIL WITH BAKING ON PREMISES",
                    "10100",
                    coverage.gl_premium_basis,
                    money(exposure_per_site),
                ),
                _HAZARD_COLUMNS,
            )
        )
    lines.extend(
        [
            "-" * 88,
            f"{'TOTAL EXPOSURE'.ljust(74)}{money(coverage.gl_exposure_usd).rjust(14)}",
            "",
            "PREMIUM BASIS LEGEND: "
            + ", ".join(f"{key} = {value}" for key, value in _BASIS_LEGEND.items()),
            band("general liability questions"),
            'EXPLAIN ALL "YES" RESPONSES'.ljust(76) + "YES  NO",
        ]
    )
    for question, answer in _GL_QUESTIONS:
        lines.append(f"{question.ljust(76)}{box(answer)}  {box(not answer)}")

    lines.extend(
        [
            band("remarks"),
            *wrap(
                "Products are baked goods sold at the applicant's own outlets and delivered "
                "to third party cafes within a 40 mile radius."
            ),
            *footer("COMMERCIAL GENERAL LIABILITY SECTION"),
        ]
    )
    return document(lines)
