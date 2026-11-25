from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from submission_evals.cases import all_specs
from submission_evals.generate import build_packet

MODEL_ORDER = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")


def _label(model: str) -> str:
    return model.replace("claude-", "").replace("-5-5", " 5.5").title()


def _trial(row: dict[str, Any], record: dict[str, Any] | None) -> dict[str, Any]:
    grade = row["grade"]
    fields = []
    for field in row.get("verdict", {}).get("fields", []):
        provenance = field.get("provenance")
        fields.append(
            {
                "field": field["field"],
                "declared": field["declared"],
                "flagDecision": field["flag_decision"],
                "valueCorrect": field["value_correct"],
                "provenanceOk": None
                if provenance is None
                else all(provenance[k] for k in ("structural", "resolvable", "semantic")),
                "provenanceDetail": None if provenance is None else provenance["detail"],
                "detail": field["detail"],
            }
        )
    return {
        "caseId": row["prompt_id"],
        "model": row["requested_model"],
        "modelLabel": _label(row["requested_model"]),
        "rep": row["rep"],
        "effort": row.get("effort"),
        "passed": bool(grade["case_passed"]),
        "valueScore": grade["value_score"],
        "provenanceScore": grade["provenance_score"],
        "missedFlags": int(grade["missed_flag"]),
        "spuriousFlags": int(grade["spurious_flag"]),
        "latency": row.get("latency_s"),
        "outputTokens": row["usage"]["output_tokens"],
        "fields": fields,
        "record": record,
        "notes": (record or {}).get("packet_notes", []),
    }


def _record_for(results: Path, row: dict[str, Any]) -> dict[str, Any] | None:
    trace = results / "traces" / (
        f"{row['prompt_id']}_{row['requested_model']}_rep{row['rep']}.json"
    )
    if not trace.exists():
        return None
    turns = json.loads(trace.read_text())
    body = next((t["content"] for t in reversed(turns) if t["role"] == "assistant"), None)
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def build(results: Path) -> dict[str, Any]:
    newest: dict[tuple[str, str, int], dict[str, Any]] = {}
    for line in (results / "results.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        newest[(row["prompt_id"], row["model"], row["rep"])] = row
    rows = list(newest.values())
    trials = [_trial(row, _record_for(results, row)) for row in rows]

    by_case: dict[str, list[dict]] = defaultdict(list)
    for trial in trials:
        by_case[trial["caseId"]].append(trial)

    cases = []
    for spec in all_specs():
        case = spec.case
        packet = build_packet(spec)
        cases.append(
            {
                "id": case.case_id,
                "title": case.title,
                "short": case.short,
                "kind": case.kind,
                "exercises": case.exercises.value if case.exercises else None,
                "corruption": case.corruption,
                "facts": {
                    "lossCount": case.risk.loss_count,
                    "totalIncurred": case.risk.total_incurred_usd,
                    "totalPaid": case.risk.total_paid_usd,
                    "locationCount": case.risk.location_count,
                    "totalInsured": case.risk.total_insured_value_usd,
                    "losses": [
                        {
                            "claimNo": loss.claim_no,
                            "carrier": loss.carrier,
                            "dateOfLoss": loss.date_of_loss.strftime("%d %b %Y"),
                            "status": loss.status,
                            "paid": loss.paid_usd,
                            "reserved": loss.reserved_usd,
                            "incurred": loss.incurred_usd,
                        }
                        for loss in case.risk.losses
                    ],
                },
                "pairedWith": case.paired_with,
                "expectations": [
                    {
                        "field": e.field,
                        "outcome": e.outcome,
                        "mode": e.source_mode.value if e.source_mode else None,
                        "document": e.source_document.value if e.source_document else None,
                        "flagAlsoAcceptable": e.flag_also_acceptable,
                        "rationale": e.rationale,
                        "source": e.rationale_source,
                    }
                    for e in case.expectations
                ],
                "documents": [
                    {
                        "name": name.value,
                        "filename": packet[name][0],
                        "body": packet[name][1],
                    }
                    for name in case.documents
                ],
                "trials": sorted(
                    by_case.get(case.case_id, []),
                    key=lambda t: (MODEL_ORDER.index(t["model"]), t["rep"]),
                ),
            }
        )

    models = []
    for model in MODEL_ORDER:
        group = [t for t in trials if t["model"] == model]
        if not group:
            continue
        models.append(
            {
                "id": model,
                "label": _label(model),
                "passed": sum(1 for t in group if t["passed"]),
                "total": len(group),
            }
        )

    return {
        "generatedAt": None,
        "effort": next((t["effort"] for t in trials if t["effort"]), None),
        "reps": max((t["rep"] for t in trials), default=0) + 1,
        "models": models,
        "cases": cases,
        "totals": {
            "trials": len(trials),
            "passed": sum(1 for t in trials if t["passed"]),
        },
    }


def write(results: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(build(results), indent=1) + "\n")
    return destination
