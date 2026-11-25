from __future__ import annotations

from submission_evals.render.layout import band, money, rule, wrap
from submission_evals.render.options import PacketOptions
from submission_evals.truth import Risk


def _period(risk: Risk) -> str:
    months = (
        risk.policy.expiration_date.year - risk.policy.effective_date.year
    ) * 12 + (risk.policy.expiration_date.month - risk.policy.effective_date.month)
    day = risk.policy.effective_date.day
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(day if day < 20 else day % 10, "th")
    start = risk.policy.effective_date.strftime(f"%-d{suffix} %B %Y")
    return f"{months} months at {start}"


def _situation(risk: Risk) -> list[str]:
    if risk.location_count == 1:
        only = risk.locations[0]
        return [f"{only.street}, {only.city}, {only.state} {only.zip_code}"]
    return [
        f"{risk.location_count} locations per the attached schedule of values.",
        "Full addresses, construction and values are shown there.",
    ]


def render(risk: Risk, options: PacketOptions) -> str:
    lines: list[str] = [
        rule(),
        "MARKET REFORM CONTRACT",
        f"UNIQUE MARKET REFERENCE: {options.market_reference}",
        rule(),
        "",
        band("RISK DETAILS"),
        "",
        f"TYPE:            {options.slip_type}",
        f"INSURED:         {risk.applicant.name}",
        f"INSURED'S STATUS: {risk.applicant.entity_type}",
        *(
            [f"REGISTERED NO:   {options.company_number}"]
            if options.company_number
            else []
        ),
        *(
            [f"FEDERAL TAX ID:  {risk.applicant.fein}"]
            if risk.applicant.fein
            else []
        ),
        f"ADDRESS:         {risk.applicant.street}, {risk.applicant.city}"
        + (f", {risk.applicant.state}" if risk.applicant.state else "")
        + f" {risk.applicant.zip_code}",
        f"CURRENCY:        {options.slip_currency}",
        f"PERIOD:          {_period(risk)}",
        "INTEREST:        Buildings, Contents and Business Interruption",
        f"SUM INSURED:     {money(risk.total_insured_value_usd)} total, "
        f"{risk.coverage.property_valuation_basis} basis",
        f"CONDITIONS:      {risk.coverage.property_coinsurance_pct}% coinsurance",
        f"                 Deductible {money(risk.coverage.property_deductible_usd)} "
        "each and every loss",
        "SITUATION:",
    ]
    lines += [f"                 {line}" for line in _situation(risk)]
    lines += [
        "",
        "LIABILITY SECTION:",
        f"                 Limit of Indemnity {money(risk.coverage.gl_each_occurrence_usd)} "
        "any one occurrence",
        f"                 Aggregate {money(risk.coverage.gl_general_aggregate_usd)} "
        "in the annual period",
        "",
        band("INFORMATION"),
        "",
    ]

    if risk.losses:
        lines.append("CLAIMS EXPERIENCE:")
        lines.append(
            f"                 {risk.loss_count} "
            f"{'claim' if risk.loss_count == 1 else 'claims'} in the period, "
            "see attached carrier listings for detail."
        )
        lines.append(
            "                 Figures in this slip are indicative only. The attached "
            "listings govern."
        )
    else:
        lines.append("CLAIMS EXPERIENCE:")
        lines.append("                 None advised by the Insured for the period.")

    lines += [
        "",
        "BUSINESS DESCRIPTION:",
    ]
    lines += [f"                 {line}" for line in wrap(risk.operations.description)]
    lines += [
        f"                 Established {risk.applicant.business_started:%-d %B %Y}, "
        f"{risk.operations.employee_count} employees, "
        f"turnover {money(risk.operations.annual_revenue_usd)}.",
        "",
        band("SECURITY DETAILS"),
        "",
        "(RE)INSURERS LIABILITY:  Several and not joint",
        "ORDER HEREON:            100% of 100%",
        f"BROKER:                  {options.agency}",
        f"CONTACT:                 {options.broker_name}, {options.broker_email}",
        rule(),
    ]
    return "\n".join(lines) + "\n"
