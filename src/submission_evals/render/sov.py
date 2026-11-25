from __future__ import annotations

import csv
import io

from submission_evals.render.layout import document, money, table_header, table_row
from submission_evals.render.options import PacketOptions, us_date
from submission_evals.truth import Risk

HEADERS = (
    "Loc",
    "Street",
    "City",
    "State",
    "Zip",
    "Construction Class",
    "Year Built",
    "Stories",
    "Square Feet",
    "Building",
    "Business Personal Property",
    "Business Income",
    "Occupancy",
    "Sprinklered",
    "Protection Class",
)

_PAGED_COLUMNS = (
    ("LOC", 5),
    ("STREET", 24),
    ("CITY", 14),
    ("ST", 4),
    ("ZIP", 7),
    ("CON", 5),
    ("BUILT", 7),
    ("SQ FT", 8),
    ("BUILDING", 12),
    ("CONTENTS", 11),
    ("BUS INCOME", 12),
)

_LEFT_COLUMNS = _PAGED_COLUMNS[:5]
_RIGHT_COLUMNS = _PAGED_COLUMNS[5:]


def _row_values(location, options: PacketOptions) -> tuple:
    return (
        location.loc_no,
        location.street,
        location.city,
        location.state,
        location.zip_code,
        location.construction_class,
        location.year_built,
        money(location.square_feet),
        money(_building_value(location, options)),
        money(location.bpp_value_usd),
        money(location.business_income_value_usd),
    )


def render_csv(risk: Risk, options: PacketOptions) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HEADERS)
    for location in risk.locations:
        writer.writerow(
            [
                location.loc_no,
                location.street,
                location.city,
                location.state,
                location.zip_code,
                location.construction_class,
                location.year_built,
                location.stories,
                location.square_feet,
                _building_value(location, options),
                location.bpp_value_usd,
                location.business_income_value_usd,
                location.occupancy,
                "Y" if location.sprinklered else "N",
                location.protection_class,
            ]
        )
    return buffer.getvalue()


def _page_header(
    risk: Risk, options: PacketOptions, page: int, with_columns: bool, feed: bool = False
) -> list[str]:
    head = [
        f"{chr(12) if feed else ''}STATEMENT OF VALUES{'':>20}{risk.applicant.name}",
        f"AS AT {us_date(options.submitted_on)}{'':>26}PAGE {page}",
        "",
    ]
    if with_columns:
        head.extend(table_header(_PAGED_COLUMNS))
    return head


def render_paged_text(risk: Risk, options: PacketOptions) -> str:
    break_after = options.sov_page_break_after
    lines = _page_header(risk, options, 1, with_columns=True)

    for location in risk.locations[:break_after]:
        lines.append(table_row(_row_values(location, options), _PAGED_COLUMNS))

    split = risk.locations[break_after]
    values = _row_values(split, options)
    lines.append(table_row(values[:5], _LEFT_COLUMNS))
    lines.append("")
    lines.extend(_page_header(risk, options, 2, with_columns=False, feed=True))
    lines.append(table_row(values[5:], _RIGHT_COLUMNS))

    for location in risk.locations[break_after + 1 :]:
        lines.append(table_row(_row_values(location, options), _PAGED_COLUMNS))

    lines.append("")
    return document(lines)


def _building_value(location, options: PacketOptions) -> int:
    if options.stale_location_values and location.loc_no == 1:
        return location.building_value_usd - 500_000
    return location.building_value_usd


def render(risk: Risk, options: PacketOptions) -> tuple[str, str]:
    if options.sov_as_paged_text:
        return "sov.txt", render_paged_text(risk, options)
    return "sov.csv", render_csv(risk, options)
