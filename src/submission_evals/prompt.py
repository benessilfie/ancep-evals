from __future__ import annotations

from submission_evals.generate import CaseSpec, build_packet

SYSTEM = """\
You are reviewing an inbound commercial insurance submission for a broker's placing team and \
producing the structured record their system will hold.

You will be given every document in the packet. Read all of them before you answer. Documents in \
a submission are written by different parties at different times, so they disagree with each \
other, and packets are sometimes incomplete.

For every field, return one of two things.

An extracted answer, when you can establish the value from the packet. Give the value, and a \
source saying which document it came from and whether you read it directly or worked it out. Use \
mode "read" only when the value itself appears in that document. Use mode "derived" when you \
computed it, and list the inputs you computed it from.

A flag, when you cannot establish a single defensible value. Give the reason, cite the documents \
that disagree, and say what should happen next: query the broker, refer to an underwriter, or \
reject the submission. Only record that the applicant misrepresented something if the packet \
shows intent rather than inconsistency.

A value of zero is an answer, not a flag. Where the packet establishes that something is nil, \
extract zero and cite the document that establishes it.

Do not guess in order to fill a field, and do not flag a field you can actually establish. Both \
are failures.

You are also given the submissions already on file for this carrier, as the document \
records_on_file. Use those, and only those, to \
decide whether this packet is a new risk or an update to one already received. An empty list \
means nothing matching is on file.

is_update_of_prior_submission takes exactly true or false and nothing else. Put the \
reasoning in the locator or in packet_notes.

Money fields are whole US dollars with no symbols or separators. Dates are ISO format, \
YYYY-MM-DD. Put anything the placing team should know, that no field covers, in packet_notes."""


def records_on_file_text(spec: CaseSpec) -> str:
    on_file = spec.case.records_on_file
    if not on_file:
        return "SUBMISSIONS ALREADY ON FILE (0):\n  none"
    rows = "\n".join(
        f"  {record.reference} | {record.named_insured} | FEIN {record.fein} | "
        f"inception {record.effective_date.isoformat()} | "
        f"received {record.received.isoformat()} | "
        f"TIV {record.total_insured_value_usd} | revenue {record.annual_revenue_usd}"
        for record in on_file
    )
    return f"SUBMISSIONS ALREADY ON FILE ({len(on_file)}):\n{rows}"


def user_content(spec: CaseSpec) -> list[dict]:
    packet = build_packet(spec)
    blocks: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Submission packet with {len(packet)} documents. "
                "Each document is given with the name the record should cite it by."
            ),
        },
    ]
    for name in spec.case.documents:
        filename, body = packet[name]
        blocks.append(
            {
                "type": "text",
                "text": f"<document name=\"{name.value}\" file=\"{filename}\">\n{body}</document>",
            }
        )
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    blocks.append(
        {
            "type": "text",
            "text": (
                "Produce the extracted record for this submission. "
                "Answer every field, with a source on every extracted value."
            ),
        }
    )
    return blocks


def system_blocks() -> list[dict]:
    return [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]


def prompt_text(spec: CaseSpec) -> str:
    return "\n\n".join(block["text"] for block in user_content(spec))
