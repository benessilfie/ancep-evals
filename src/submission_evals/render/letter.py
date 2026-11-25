from __future__ import annotations

from submission_evals.render.layout import document, wrap
from submission_evals.render.options import PacketOptions, long_date, us_date
from submission_evals.truth import Risk


def _one(risk: Risk, letter) -> list[str]:
    return [
        letter.carrier.upper(),
        "Commercial Lines Claims Services",
        "4400 Cadwell Plaza, Hartford CT 06103",
        "",
        long_date(letter.issued),
        "",
        "To whom it may concern",
        "",
        f"RE: {risk.applicant.name}",
        f"    Policy {letter.policy_no}",
        f"    {us_date(letter.period_start)} to {us_date(letter.period_end)}",
        "",
        *wrap(
            "We confirm that no claims have been reported, paid or reserved under the "
            "policy referenced above for the period stated. This confirmation is given "
            f"as at the valuation date of {long_date(letter.issued)} and is issued in "
            "place of a nil claims experience report."
        ),
        "",
        *wrap(
            "This letter reflects our claim records as at the date shown. It does not "
            "extend to incidents which have occurred but have not been reported to us."
        ),
        "",
        "Yours faithfully",
        "",
        "R. Castellan",
        "Claims Services Manager",
        letter.carrier,
    ]


def render(risk: Risk, options: PacketOptions) -> str:
    if not risk.no_losses_letters:
        raise ValueError("no_losses_letters is empty on this risk")
    lines: list[str] = []
    for index, letter in enumerate(risk.no_losses_letters):
        if index:
            lines.extend(["", "=" * 96, ""])
        lines.extend(_one(risk, letter))
    return document(lines)
