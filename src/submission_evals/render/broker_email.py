from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from submission_evals.manifest import attachment_lines
from submission_evals.render.layout import money, wrap
from submission_evals.render.options import PacketOptions
from submission_evals.truth import Risk


@dataclass(frozen=True)
class Message:
    sent: str
    sender: str
    recipient: str
    subject: str
    body: list[str]


def _covering_message(risk: Risk, options: PacketOptions, total: int | None) -> Message:
    applicant = risk.applicant
    cities = sorted({location.city for location in risk.locations})
    body = wrap(
        f"Morning, new business submission attached for {applicant.name}, "
        f"{risk.location_count} retail bakery locations across "
        f"{', '.join(cities[:-1])} and {cities[-1]}, property and general liability, "
        f"incepting {risk.policy.effective_date.day} {risk.policy.effective_date.strftime('%B')}."
    )
    body.append("")
    second = (
        f"Revenue is ${money(risk.operations.annual_revenue_usd)} and "
        f"{risk.operations.employee_count} staff. Expiring is with "
        f"{risk.prior_carriers[0].carrier} on the property at "
        f"${money(risk.prior_carriers[0].premium_usd)} and "
        f"{risk.prior_carriers[1].carrier} on the liability at "
        f"${money(risk.prior_carriers[1].premium_usd)}."
    )
    if total is not None:
        second = f"Total sum insured across the schedule is ${money(total)}. " + second
    body.extend(wrap(second))
    body.append("")

    if options.include_no_losses_letter:
        body.extend(
            wrap(
                "Clean on claims, no losses in the last five years, the carrier's "
                "confirmation letter is attached in place of a nil loss run."
            )
        )
    elif not options.include_loss_runs:
        body.extend(
            wrap(
                "I have asked both carriers for the loss runs and will forward them "
                "as soon as they land."
            )
        )
    else:
        body.extend(
            wrap(
                f"{risk.loss_count} claims in the last five years, both on the loss runs attached."
            )
        )
    body.append("")
    if options.resend_note:
        body.extend(wrap(options.resend_note))
        body.append("")
    body.append("Attached:")
    body.extend(f"  - {item}" for item in attachment_lines(risk, options))
    body.append("")
    body.append(options.broker_name)
    body.append(options.agency)

    return Message(
        sent=options.submitted_on.strftime("%a, %d %b %Y %H:%M GMT").replace("00:00", "09:14"),
        sender=f"{options.broker_name} <{options.broker_email}>",
        recipient=f"Underwriting <{options.underwriter_email}>",
        subject=(
            f"New business submission - {risk.applicant.name} - "
            f"inception {risk.policy.effective_date.strftime('%d/%m/%Y')}"
        ),
        body=body,
    )


def _correction_thread(risk: Risk, options: PacketOptions) -> list[Message]:
    first_location = risk.locations[0]
    stale_building = first_location.building_value_usd - 500_000
    insured_contact = f"Ama Dadson <finance@{_domain(risk)}>"
    return [
        Message(
            sent="Fri, 04 Dec 2026 16:41 GMT",
            sender=insured_contact,
            recipient=f"{options.broker_name} <{options.broker_email}>",
            subject=f"RE: {risk.applicant.name} renewal - schedule",
            body=wrap(
                f"One correction before this goes out. We had the "
                f"{first_location.city} building revalued in October and it came back "
                f"at ${money(first_location.building_value_usd)}, not the "
                f"${money(stale_building)} that was on last year's schedule. That takes "
                f"the total sum insured to ${money(risk.total_insured_value_usd)}. "
                "Everything else is unchanged."
            ),
        ),
        Message(
            sent="Thu, 03 Dec 2026 11:08 GMT",
            sender=f"{options.broker_name} <{options.broker_email}>",
            recipient=insured_contact,
            subject=f"{risk.applicant.name} renewal - schedule",
            body=wrap(
                "Can you confirm the values on the schedule are still right before I "
                "go to market, particularly the buildings."
            ),
        ),
    ]


def _domain(risk: Risk) -> str:
    slug = "".join(ch for ch in risk.applicant.name.lower() if ch.isalnum())
    return f"{slug[:18]}.example"


def _render_message(message: Message, depth: int) -> list[str]:
    prefix = "> " * depth
    header = [
        f"{prefix}From: {message.sender}",
        f"{prefix}To: {message.recipient}",
        f"{prefix}Date: {message.sent}",
        f"{prefix}Subject: {message.subject}",
        prefix.rstrip(),
    ]
    return header + [f"{prefix}{line}".rstrip() for line in message.body]


def render(risk: Risk, options: PacketOptions) -> str:
    total: int | None = None
    if options.stale_total_in_email is not None:
        total = options.stale_total_in_email
    elif options.state_total_in_email:
        total = risk.total_insured_value_usd

    messages = [_covering_message(risk, options, total)]
    if options.stale_total_in_email is not None:
        messages.extend(_correction_thread(risk, options))

    lines: list[str] = []
    for depth, message in enumerate(messages):
        if depth:
            lines.append("")
            lines.append("> " * depth + "-----Original Message-----")
        lines.extend(_render_message(message, depth))
    return "\n".join(lines) + "\n"


def inception_day(value: date) -> str:
    return value.strftime("%d %B %Y")
