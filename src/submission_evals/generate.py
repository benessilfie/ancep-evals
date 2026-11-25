from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from submission_evals.manifest import documents_for  # noqa: F401
from submission_evals.render import (
    application,
    broker_email,
    letter,
    liability_section,
    loss_run,
    property_section,
    sov,
)
from submission_evals.render.options import PacketOptions
from submission_evals.truth import Case, DocumentName

_FILENAMES = {
    DocumentName.BROKER_EMAIL: "broker_email.txt",
    DocumentName.APPLICATION: "application.txt",
    DocumentName.PROPERTY_SECTION: "property_section.txt",
    DocumentName.LIABILITY_SECTION: "liability_section.txt",
    DocumentName.LOSS_RUN_A: "loss_run_a.csv",
    DocumentName.LOSS_RUN_B: "loss_run_b.txt",
    DocumentName.NO_LOSSES_LETTER: "no_losses_letter.txt",
    DocumentName.RECORDS_ON_FILE: "records_on_file.txt",
}


@dataclass(frozen=True)
class CaseSpec:
    case: Case
    options: PacketOptions


def build_packet(spec: CaseSpec) -> dict[DocumentName, tuple[str, str]]:
    from submission_evals.prompt import records_on_file_text

    risk, options = spec.case.risk, spec.options
    packet: dict[DocumentName, tuple[str, str]] = {
        DocumentName.RECORDS_ON_FILE: (
            _FILENAMES[DocumentName.RECORDS_ON_FILE],
            records_on_file_text(spec) + "\n",
        ),
        DocumentName.BROKER_EMAIL: (
            _FILENAMES[DocumentName.BROKER_EMAIL],
            broker_email.render(risk, options),
        ),
        DocumentName.APPLICATION: (
            _FILENAMES[DocumentName.APPLICATION],
            application.render(risk, options),
        ),
        DocumentName.PROPERTY_SECTION: (
            _FILENAMES[DocumentName.PROPERTY_SECTION],
            property_section.render(risk, options),
        ),
        DocumentName.LIABILITY_SECTION: (
            _FILENAMES[DocumentName.LIABILITY_SECTION],
            liability_section.render(risk, options),
        ),
    }
    packet[DocumentName.SOV] = sov.render(risk, options)

    for index, (filename, body) in enumerate(loss_run.render_all(risk, options)):
        name = DocumentName.LOSS_RUN_A if index == 0 else DocumentName.LOSS_RUN_B
        packet[name] = (filename, body)

    if options.include_no_losses_letter:
        packet[DocumentName.NO_LOSSES_LETTER] = (
            _FILENAMES[DocumentName.NO_LOSSES_LETTER],
            letter.render(risk, options),
        )

    declared = set(spec.case.documents)
    built = set(packet)
    if declared != built:
        raise ValueError(
            f"{spec.case.case_id}: case declares {sorted(d.value for d in declared)} "
            f"but the packet holds {sorted(d.value for d in built)}"
        )
    return packet


def packet_text(spec: CaseSpec) -> dict[DocumentName, str]:
    return {name: body for name, (_, body) in build_packet(spec).items()}


def write_packet(spec: CaseSpec, root: Path) -> Path:
    directory = root / spec.case.case_id
    directory.mkdir(parents=True, exist_ok=True)
    packet = build_packet(spec)
    for _, (filename, body) in sorted(packet.items()):
        (directory / filename).write_text(body)

    truth = spec.case.risk.model_dump(mode="json")
    (directory / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")

    expectations = {
        "case_id": spec.case.case_id,
        "title": spec.case.title,
        "kind": spec.case.kind,
        "exercises": spec.case.exercises.value if spec.case.exercises else None,
        "paired_with": spec.case.paired_with,
        "documents": [name.value for name in spec.case.documents],
        "expectations": [
            expectation.model_dump(mode="json") for expectation in spec.case.expectations
        ],
    }
    (directory / "expected.json").write_text(json.dumps(expectations, indent=2) + "\n")
    return directory


def write_all(specs: list[CaseSpec], root: Path) -> list[Path]:
    return [write_packet(spec, root) for spec in specs]
