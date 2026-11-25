from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import time
import uuid
import zipfile
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, NamedTuple

import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.datastructures import UploadFile

from submission_evals.cases import all_specs
from submission_evals.checks import run_all
from submission_evals.classify import assign
from submission_evals.extract import GRADED_FIELDS, ExtractedSubmission
from submission_evals.generate import build_packet
from submission_evals.grade import grade
from submission_evals.prompt import SYSTEM, system_blocks
from submission_evals.truth import DocumentName

LIVE_EFFORT = "medium"
MAX_TOKENS = 32_000
MAX_FILES = 12
MAX_BYTES = 400_000


class ModelLimit(NamedTuple):
    label: str
    note: str
    per_hour: int
    per_day: int
    usd: float


LIVE_MODELS: dict[str, ModelLimit] = {
    "claude-haiku-5-5": ModelLimit("Haiku 5.5", "fastest, cheapest", 12, 36, 0.057),
    "claude-sonnet-5-5": ModelLimit("Sonnet 5.5", "the middle one", 6, 12, 0.085),
    "claude-opus-5-5": ModelLimit("Opus 5.5", "most capable", 3, 6, 0.452),
}
DEFAULT_MODEL = "claude-haiku-5-5"

def _load_env_file() -> None:
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file()

logger = logging.getLogger("submission_evals")

app = FastAPI(title="submission intake evals")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("DEMO_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

SPECS = {spec.case.case_id: spec for spec in all_specs()}
_recent: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_today: dict[str, deque[float]] = defaultdict(deque)
_runs: dict[str, dict[str, Any]] = {}


def _prune(bucket: deque[float], now: float, window: float) -> None:
    while bucket and now - bucket[0] > window:
        bucket.popleft()


def _available(model: str) -> bool:
    limit = LIVE_MODELS[model]
    _prune(_today[model], time.time(), 86_400)
    return len(_today[model]) < limit.per_day


def _allow(ip: str, model: str) -> str | None:
    limit = LIVE_MODELS[model]
    now = time.time()
    hour = _recent[(ip, model)]
    _prune(hour, now, 3600)
    _prune(_today[model], now, 86_400)
    if len(_today[model]) >= limit.per_day:
        return (
            f"{limit.label} is not available right now. Try another model, "
            "or the 90 recorded runs on the findings tab."
        )
    if len(hour) >= limit.per_hour:
        return (
            f"{limit.label} is not available from this address right now. "
            "Try another model, or the 90 recorded runs on the findings tab."
        )
    hour.append(now)
    _today[model].append(now)
    return None


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "default": DEFAULT_MODEL,
        "models": [
            {
                "id": model,
                "label": limit.label,
                "note": limit.note,
                "available": _available(model),
            }
            for model, limit in LIVE_MODELS.items()
        ],
    }


@app.get("/api/packets")
def packets() -> list[dict[str, Any]]:
    out = []
    for spec in all_specs():
        built = build_packet(spec)
        out.append(
            {
                "id": spec.case.case_id,
                "title": spec.case.title,
                "kind": spec.case.kind,
                "files": [built[name][0] for name in spec.case.documents],
                "bytes": sum(len(built[name][1]) for name in spec.case.documents),
            }
        )
    return out


@app.get("/api/packets/{case_id}/download")
def download(case_id: str) -> StreamingResponse:
    spec = SPECS.get(case_id)
    if spec is None:
        raise HTTPException(404, "no such packet")
    built = build_packet(spec)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in spec.case.documents:
            filename, body = built[name]
            archive.writestr(filename, body)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{case_id}.zip"'},
    )


@app.post("/api/runs")
async def create_run(request: Request) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"

    form = await request.form()
    requested = form.get("model")
    model = requested if isinstance(requested, str) and requested in LIVE_MODELS else DEFAULT_MODEL

    refusal = _allow(client_ip, model)
    if refusal:
        raise HTTPException(429, refusal)

    packet_id = form.get("packet_id")
    packet: dict[DocumentName, str] = {}
    unknown: list[dict] = []

    if isinstance(packet_id, str) and packet_id:
        spec = SPECS.get(packet_id)
        if spec is None:
            raise HTTPException(404, "no such packet")
        packet = {name: body for name, (_, body) in build_packet(spec).items()}
    else:
        uploads = [v for v in form.getlist("files") if isinstance(v, UploadFile)]
        if not uploads:
            raise HTTPException(400, "send packet_id or at least one file")
        if len(uploads) > MAX_FILES:
            raise HTTPException(400, f"at most {MAX_FILES} files")
        payload: list[tuple[str, bytes]] = []
        for upload in uploads:
            raw = await upload.read()
            if len(raw) > MAX_BYTES:
                raise HTTPException(400, f"{upload.filename} is too large")
            payload.append((upload.filename or "unnamed", raw))
        packet, unknown = assign(payload)
        if not packet:
            raise HTTPException(
                400,
                "could not recognise any of those as submission documents. "
                "Plain text, CSV and PDF are read; scans without a text layer are not.",
            )

    run_id = uuid.uuid4().hex[:12]
    _runs[run_id] = {
        "packet": packet,
        "packet_id": packet_id if isinstance(packet_id, str) else None,
        "unknown": unknown,
        "model": model,
    }
    return {"run_id": run_id}


def _sse(event: str, payload: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


async def _stream(run_id: str) -> AsyncIterator[str]:
    state = _runs.pop(run_id, None)
    if state is None:
        yield _sse("error", {"message": "that run has already been streamed"})
        return

    packet: dict[DocumentName, str] = state["packet"]
    yield _sse(
        "stage",
        {
            "stage": "received",
            "documents": [name.value for name in packet],
            "unknown": state["unknown"],
        },
    )

    blocks: list[dict[str, Any]] = [
        {"type": "text", "text": f"Submission packet with {len(packet)} documents."}
    ]
    for name, body in packet.items():
        blocks.append(
            {"type": "text", "text": f'<document name="{name.value}">\n{body}</document>'}
        )
    blocks.append(
        {
            "type": "text",
            "text": "Produce the extracted record. Answer every field, with a source.",
        }
    )

    yield _sse("stage", {"stage": "reading", "model": state["model"]})
    started = time.monotonic()

    try:
        client = anthropic.AsyncAnthropic()
        async with client.messages.stream(
            model=state["model"],
            max_tokens=MAX_TOKENS,
            system=system_blocks(),
            messages=[{"role": "user", "content": blocks}],
            output_config={
                "effort": LIVE_EFFORT,
                "format": {
                    "type": "json_schema",
                    "schema": ExtractedSubmission.model_json_schema(),
                },
            },
        ) as stream:
            response = await stream.get_final_message()
    except Exception as error:  # noqa: BLE001
        logger.exception("model call failed")
        yield _sse("error", {"message": f"the model call failed: {type(error).__name__}"})
        return

    if response.stop_reason == "refusal":
        yield _sse("error", {"message": "the model declined this packet"})
        return

    body = "".join(b.text for b in response.content if b.type == "text")
    try:
        produced = ExtractedSubmission.model_validate_json(body)
    except Exception:  # noqa: BLE001
        yield _sse("error", {"message": "the model returned something unreadable"})
        return

    elapsed = round(time.monotonic() - started, 1)
    yield _sse(
        "stage",
        {"stage": "extracted", "seconds": elapsed, "tokens": response.usage.output_tokens},
    )

    for field in GRADED_FIELDS:
        answer = getattr(produced, field)
        yield _sse("field", {"field": field, "answer": answer.model_dump(mode="json")})
        await asyncio.sleep(0.03)

    yield _sse("stage", {"stage": "checking"})
    findings = run_all(produced, packet)
    for finding in findings:
        yield _sse("finding", finding.model_dump(mode="json"))
        await asyncio.sleep(0.05)

    graded = None
    if state["packet_id"]:
        spec = SPECS[state["packet_id"]]
        verdict = grade(spec.case, produced, packet_text=packet)
        graded = {
            "passed": verdict.case_passed,
            "valueScore": verdict.value_score,
            "provenanceScore": verdict.provenance_score,
        }

    yield _sse(
        "done",
        {
            "seconds": elapsed,
            "blocking": sum(1 for f in findings if f.severity == "blocking"),
            "queries": sum(1 for f in findings if f.severity == "query"),
            "notes": produced.packet_notes,
            "graded": graded,
        },
    )


@app.get("/api/runs/{run_id}/events")
async def events(run_id: str) -> StreamingResponse:
    return StreamingResponse(
        _stream(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


SYSTEM_PROMPT = SYSTEM
