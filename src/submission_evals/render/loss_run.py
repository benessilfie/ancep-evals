from __future__ import annotations

import csv
import io
from datetime import date

from submission_evals.render.layout import document, money, table_row
from submission_evals.render.options import PacketOptions, carrier_date, us_date
from submission_evals.truth import Loss, PriorCarrier, Risk

_EXPERIENCE_YEARS = 5

_CALLAGHAN_COLUMNS = (
    ("CLAIM NO", 11),
    ("DATE OF OCCURRENCE", 20),
    ("REPORTED", 13),
    ("STATUS", 8),
    ("CAUSE OF LOSS", 16),
    ("LOSS PAID", 12),
    ("OUTSTANDING", 13),
    ("TOTAL INCURRED", 15),
)

_CALLAGHAN_WIDTH = sum(width for _, width in _CALLAGHAN_COLUMNS)


def _experience_start(risk: Risk) -> date:
    valuation = risk.loss_run_valuation_date or risk.policy.effective_date
    return date(valuation.year - _EXPERIENCE_YEARS, 1, 1)


def _losses_for(risk: Risk, carrier: PriorCarrier) -> list[Loss]:
    return [loss for loss in risk.losses if loss.carrier == carrier.carrier]


def render_meridian(risk: Risk, carrier: PriorCarrier, options: PacketOptions) -> str:
    valuation = risk.loss_run_valuation_date
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([carrier.carrier.upper()])
    writer.writerow(["CLAIMS EXPERIENCE REPORT"])
    writer.writerow([])
    writer.writerow(["Named Insured", risk.applicant.name])
    writer.writerow(["Policy Number", carrier.policy_no])
    writer.writerow(["Line of Coverage", carrier.line])
    writer.writerow(
        [
            "Experience Period",
            f"{us_date(_experience_start(risk))} to {us_date(valuation)}",
        ]
    )
    writer.writerow(["Valuation Date", us_date(valuation)])
    writer.writerow([])
    writer.writerow(
        [
            "Claim Number",
            "Date of Loss",
            "Date Reported",
            "Status",
            "Cause",
            "Description",
            "Paid",
            "Reserved",
            "Incurred",
        ]
    )
    losses = _losses_for(risk, carrier)
    for loss in losses:
        writer.writerow(
            [
                loss.claim_no,
                us_date(loss.date_of_loss),
                us_date(loss.date_reported),
                loss.status.capitalize(),
                loss.cause,
                loss.description,
                loss.paid_usd,
                loss.reserved_usd,
                loss.incurred_usd,
            ]
        )
    writer.writerow([])
    writer.writerow(
        [
            "Totals",
            "",
            "",
            "",
            "",
            f"{len(losses)} claims",
            sum(loss.paid_usd for loss in losses),
            sum(loss.reserved_usd for loss in losses),
            sum(loss.incurred_usd for loss in losses),
        ]
    )
    return buffer.getvalue()


def render_callaghan(risk: Risk, carrier: PriorCarrier, options: PacketOptions) -> str:
    valuation = risk.loss_run_valuation_date
    losses = _losses_for(risk, carrier)
    lines = [
        carrier.carrier.upper(),
        "LOSS EXPERIENCE LISTING",
        "=" * _CALLAGHAN_WIDTH,
        f"INSURED.........: {risk.applicant.name.upper()}",
        f"POLICY..........: {carrier.policy_no}",
        f"COVERAGE........: {carrier.line.upper()}",
        f"EXPERIENCE FROM.: {carrier_date(_experience_start(risk))}",
        f"EVALUATED AS OF.: {carrier_date(valuation)}",
        "=" * _CALLAGHAN_WIDTH,
        "",
        table_row([n for n, _ in _CALLAGHAN_COLUMNS], _CALLAGHAN_COLUMNS),
        "-" * _CALLAGHAN_WIDTH,
    ]
    for loss in losses:
        paid = loss.incurred_usd if options.mislabel_loss_run_b_columns else loss.paid_usd
        lines.append(
            table_row(
                (
                    loss.claim_no,
                    carrier_date(loss.date_of_loss),
                    carrier_date(loss.date_reported),
                    loss.status.upper(),
                    loss.cause.upper(),
                    money(paid),
                    money(loss.reserved_usd),
                    money(loss.incurred_usd),
                ),
                _CALLAGHAN_COLUMNS,
            )
        )
    lines.extend(
        [
            "-" * _CALLAGHAN_WIDTH,
            f"{len(losses)} CLAIM(S) LISTED",
            "",
            "NOTE: OUTSTANDING AMOUNTS ARE ADJUSTER ESTIMATES AT THE EVALUATION DATE",
            "AND ARE SUBJECT TO CHANGE. FIGURES ARE GROSS OF ANY RECOVERY.",
        ]
    )
    return document(lines)


_RENDERERS = {"property": render_meridian, "general liability": render_callaghan}


def render_all(risk: Risk, options: PacketOptions) -> list[tuple[str, str]]:
    if not options.include_loss_runs:
        return []
    documents: list[tuple[str, str]] = []
    for index, carrier in enumerate(risk.prior_carriers):
        renderer = _RENDERERS[carrier.line.casefold()]
        suffix = "a" if index == 0 else "b"
        extension = "csv" if renderer is render_meridian else "txt"
        documents.append((f"loss_run_{suffix}.{extension}", renderer(risk, carrier, options)))
    return documents
