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

_GENERAL_QUESTIONS = (
    ("1a. IS THE APPLICANT A SUBSIDIARY OF ANOTHER ENTITY?", False),
    ("1b. DOES THE APPLICANT HAVE ANY SUBSIDIARIES?", False),
    ("2. IS A FORMAL SAFETY PROGRAM IN OPERATION?", True),
    ("3. ANY EXPOSURE TO FLAMMABLES, EXPLOSIVES, CHEMICALS?", False),
    ("4. ANY CATASTROPHE EXPOSURE?", False),
    ("5. ANY OTHER INSURANCE WITH THIS COMPANY?", False),
    ("6. ANY POLICY DECLINED OR NON-RENEWED IN THE PRIOR 3 YEARS?", False),
    ("7. ANY PAST LOSSES RELATING TO DISCRIMINATION OR NEGLIGENT HIRING?", False),
    ("8. ANY ARSON OR FRAUD CONVICTION IN THE LAST FIVE YEARS?", False),
    ("9. ANY UNCORRECTED FIRE CODE VIOLATIONS?", False),
    ("10. ANY BANKRUPTCIES, TAX OR CREDIT LIENS IN THE PAST 5 YEARS?", False),
    ("11. HAS BUSINESS BEEN PLACED IN A TRUST?", False),
    ("12. ANY FOREIGN OPERATIONS OR PRODUCTS SOLD ABROAD?", False),
)

_PREMISES_COLUMNS = (
    ("LOC#", 5),
    ("BLD#", 5),
    ("STREET, CITY, COUNTY, STATE, ZIP+4", 54),
    ("CITY LIMITS", 12),
    ("INTEREST", 10),
    ("%OCC", 5),
)

_LOSS_COLUMNS = (
    ("DATE OF", 12),
    ("LINE", 10),
    ("TYPE/DESCRIPTION OF OCCURRENCE OR CLAIM", 32),
    ("DATE OF", 12),
    ("AMOUNT", 10),
    ("AMOUNT", 10),
    ("CLAIM", 6),
)

_LOSS_SUBHEAD = (
    ("OCCURRENCE", 12),
    ("", 10),
    ("", 32),
    ("CLAIM", 12),
    ("PAID", 10),
    ("RESERVED", 10),
    ("STATUS", 6),
)

_PRIOR_COLUMNS = (
    ("LINE", 24),
    ("CARRIER", 24),
    ("POLICY NUMBER", 18),
    ("EFF-EXP DATE", 24),
    ("PREMIUM", 10),
)


def _lines_requested(risk: Risk) -> list[str]:
    wanted = {line.casefold() for line in risk.policy.lines_requested}
    options = (
        ("PROPERTY", "property"),
        ("COMMERCIAL GENERAL LIABILITY", "commercial general liability"),
        ("BUSINESS AUTO", "business auto"),
        ("WORKERS COMPENSATION", "workers compensation"),
        ("UMBRELLA", "umbrella"),
        ("CRIME/MISCELLANEOUS CRIME", "crime"),
    )
    rendered = []
    for index in range(0, len(options), 2):
        pair = options[index : index + 2]
        rendered.append(row(*(ticked(key in wanted, label, 48) for label, key in pair)))
    return rendered


def render(risk: Risk, options: PacketOptions) -> str:
    applicant = risk.applicant
    operations = risk.operations
    policy = risk.policy
    lines: list[str] = [
        rule(),
        centred("COMMERCIAL INSURANCE APPLICATION"),
        centred("APPLICANT INFORMATION SECTION"),
        rule(),
        row(
            cell("AGENCY", options.agency, 48),
            cell("CARRIER", risk.prior_carriers[0].carrier, 30),
            cell("DATE", us_date(options.submitted_on), 18),
        ),
        row(
            cell("AGENCY CUSTOMER ID", options.agency_customer_id, 48),
            cell("NAIC CODE", "24171", 30),
            cell("UNDERWRITER", "", 18),
        ),
        band("policies or program requested"),
        "INDICATE SECTIONS ATTACHED",
        *_lines_requested(risk),
        band("status of transaction"),
        row(
            ticked(True, "QUOTE", 24),
            ticked(False, "ISSUE POLICY", 24),
            ticked(False, "RENEW", 24),
            ticked(False, "BOUND", 24),
        ),
        row(
            cell("PROPOSED EFF DATE", us_date(policy.effective_date), 34),
            cell("PROPOSED EXP DATE", us_date(policy.expiration_date), 34),
            cell("BILLING PLAN", "AGENCY BILL", 28),
        ),
        band("applicant information"),
        row(
            cell("NAME (First Named Insured)", applicant.name, 56),
            "MAILING ADDRESS INCL ZIP+4",
        ),
        row(cell("", "", 56), cell("STREET", applicant.street, 40)),
        row(
            cell("FEIN OR SOC SEC #", applicant.fein, 56),
            cell("CITY", applicant.city, 40),
        ),
        row(
            cell("PHONE (A/C, No, Ext)", "(201) 555-0184", 56),
            cell("STATE", applicant.state, 40),
        ),
        row(
            cell("E-MAIL ADDRESS(ES)", f"accounts@{_slug(applicant.name)}.example", 56),
            cell("ZIP CODE", applicant.zip_code, 40),
        ),
        row(
            ticked(False, "INDIVIDUAL", 18),
            ticked(False, "CORPORATION", 20),
            ticked(applicant.entity_type.upper() == "LLC", "LLC", 20),
            cell("NO. OF MEMBERS AND MANAGERS", "2", 38),
        ),
        row(
            ticked(False, "PARTNERSHIP", 18),
            ticked(False, "JOINT VENTURE", 20),
            ticked(False, "NOT FOR PROFIT", 20),
            cell("DATE BUS STARTED", us_date(applicant.business_started), 38),
        ),
        band("premises information"),
        *table_header(_PREMISES_COLUMNS),
    ]

    for location in risk.locations:
        lines.append(
            table_row(
                (
                    location.loc_no,
                    1,
                    f"{location.street}, {location.city}, Hudson, "
                    f"{location.state} {location.zip_code}",
                    "INSIDE",
                    "OWNER",
                    "100",
                ),
                _PREMISES_COLUMNS,
            )
        )

    lines.extend(
        [
            band("nature of business"),
            "DESCRIPTION OF PRIMARY OPERATIONS:",
            *wrap(operations.description, indent="  "),
            row(
                cell("SIC", operations.sic_code, 24),
                cell("NAICS", operations.naics_code, 26),
                cell("ANNUAL REVENUES", money(operations.annual_revenue_usd), 40),
            ),
            row(
                cell("NO. OF FULL TIME EMPLOYEES", operations.employee_count, 40),
                cell("NO. OF PART TIME EMPLOYEES", 0, 40),
            ),
            band("general information"),
            'EXPLAIN ALL "YES" RESPONSES'.ljust(76) + "YES  NO",
        ]
    )
    for question, answer in _GENERAL_QUESTIONS:
        lines.append(f"{question.ljust(76)}{box(answer)}  {box(not answer)}")

    lines.extend([band("prior carrier information"), *table_header(_PRIOR_COLUMNS)])
    for carrier in risk.prior_carriers:
        lines.append(
            table_row(
                (
                    carrier.line.upper(),
                    carrier.carrier,
                    carrier.policy_no,
                    f"{us_date(carrier.period_start)} - {us_date(carrier.period_end)}",
                    money(carrier.premium_usd),
                ),
                _PRIOR_COLUMNS,
            )
        )

    declared = () if options.tick_no_losses_box else risk.losses
    lines.extend(
        [
            band("loss history"),
            *wrap(
                "ENTER ALL CLAIMS OR LOSSES (REGARDLESS OF FAULT AND WHETHER OR NOT "
                "INSURED) OR OCCURRENCES THAT MAY GIVE RISE TO CLAIMS FOR THE PRIOR 5 "
                "YEARS (3 YEARS IN KS & NY)"
            ),
            row(
                cell("CHK HERE IF NONE", box(options.tick_no_losses_box), 48),
                cell(
                    "SEE ATTACHED LOSS SUMMARY",
                    box(options.include_loss_runs and not options.tick_no_losses_box),
                    46,
                ),
            ),
            table_row([name for name, _ in _LOSS_COLUMNS], _LOSS_COLUMNS),
            table_row([name for name, _ in _LOSS_SUBHEAD], _LOSS_SUBHEAD),
            "-" * 92,
        ]
    )
    if not declared:
        lines.append("")
    for loss in declared:
        lines.append(
            table_row(
                (
                    us_date(loss.date_of_loss),
                    "PROPERTY" if loss.carrier == risk.prior_carriers[0].carrier else "GL",
                    loss.description,
                    us_date(loss.date_reported),
                    money(loss.paid_usd),
                    money(loss.reserved_usd),
                    "CLSD" if loss.status == "closed" else "OPEN",
                ),
                _LOSS_COLUMNS,
            )
        )

    lines.extend(
        [
            band("signature"),
            *wrap(
                "THE UNDERSIGNED IS AN AUTHORIZED REPRESENTATIVE OF THE APPLICANT AND "
                "CERTIFIES THAT THE ANSWERS ARE TRUE, CORRECT AND COMPLETE TO THE BEST "
                "OF HIS/HER KNOWLEDGE."
            ),
            row(
                cell("APPLICANT'S SIGNATURE", "A. Dadson", 48),
                cell("DATE", us_date(options.submitted_on), 20),
            ),
            row(
                cell("PRODUCER'S SIGNATURE", options.broker_name, 48),
                cell("NATIONAL PRODUCER NUMBER", "1884220", 26),
            ),
            *footer("COMMERCIAL INSURANCE APPLICATION"),
        ]
    )
    return document(lines)


def _slug(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())[:18]
