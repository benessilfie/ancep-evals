from __future__ import annotations

from submission_evals.render.options import PacketOptions
from submission_evals.truth import DocumentName, Risk

ATTACHMENT_NAMES = {
    DocumentName.APPLICATION: "application",
    DocumentName.PROPERTY_SECTION: "property section",
    DocumentName.LIABILITY_SECTION: "general liability section",
    DocumentName.SOV: "statement of values",
    DocumentName.NO_LOSSES_LETTER: "no losses letters from both expiring carriers",
}


def documents_for(risk: Risk, options: PacketOptions) -> tuple[DocumentName, ...]:
    present = [
        DocumentName.RECORDS_ON_FILE,
        DocumentName.BROKER_EMAIL,
        DocumentName.APPLICATION,
        DocumentName.PROPERTY_SECTION,
        DocumentName.LIABILITY_SECTION,
        DocumentName.SOV,
    ]
    if options.include_loss_runs:
        runs = [DocumentName.LOSS_RUN_A, DocumentName.LOSS_RUN_B]
        present.extend(runs[: len(risk.prior_carriers)])
    if options.include_no_losses_letter:
        present.append(DocumentName.NO_LOSSES_LETTER)
    return tuple(present)


def attachment_lines(risk: Risk, options: PacketOptions) -> list[str]:
    documents = documents_for(risk, options)
    items = [
        ATTACHMENT_NAMES[name]
        for name in documents
        if name in ATTACHMENT_NAMES and name is not DocumentName.NO_LOSSES_LETTER
    ]
    if DocumentName.LOSS_RUN_A in documents:
        carriers = [carrier.carrier for carrier in risk.prior_carriers]
        items.append(f"loss runs, {' and '.join(carriers)}")
    if DocumentName.NO_LOSSES_LETTER in documents:
        items.append(ATTACHMENT_NAMES[DocumentName.NO_LOSSES_LETTER])
    return items
