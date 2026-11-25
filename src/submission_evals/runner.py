from __future__ import annotations

import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
from pydantic import ValidationError

from submission_evals.extract import ExtractedSubmission
from submission_evals.generate import CaseSpec, packet_text
from submission_evals.grade import CaseVerdict, grade
from submission_evals.prompt import SYSTEM, prompt_text, system_blocks, user_content

RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


@dataclass(frozen=True)
class RunConfig:
    models: tuple[str, ...] = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
    reps: int = 3
    effort: str = "high"
    max_tokens: int = 32_000
    concurrency: int = 6
    case_timeout_s: float = 600.0
    max_attempts: int = 4
    results_dir: Path = Path("results")


@dataclass
class Attempt:
    retries: int = 0
    started: float = field(default_factory=time.monotonic)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started


def trial_key(case_id: str, model: str, rep: int) -> str:
    return f"{case_id}::{model}::rep{rep}"


def _usage_dict(usage: Any) -> dict[str, int]:
    return {
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


def _grade_metrics(verdict: CaseVerdict) -> dict[str, float]:
    counts = verdict.flag_counts
    return {
        "case_passed": float(verdict.case_passed),
        "value_score": round(verdict.value_score, 4),
        "provenance_score": round(verdict.provenance_score, 4),
        "correctly_flagged": float(counts["correctly_flagged"]),
        "correctly_not_flagged": float(counts["correctly_not_flagged"]),
        "missed_flag": float(counts["missed_flag"]),
        "spurious_flag": float(counts["spurious_flag"]),
        "loss_arithmetic_ok": float(verdict.loss_rows_arithmetic_consistent),
        "locations_ok": float(verdict.location_rows_correct),
        "refused": 0.0,
    }


def _trace(spec: CaseSpec, response: Any) -> list[dict[str, Any]]:
    thinking = "".join(
        getattr(block, "thinking", "") or ""
        for block in response.content
        if block.type == "thinking"
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    assistant: dict[str, Any] = {"role": "assistant", "content": text}
    if thinking:
        assistant["thinking"] = thinking
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt_text(spec)},
        assistant,
    ]


class Runner:
    def __init__(self, config: RunConfig, client: Any | None = None) -> None:
        self.config = config
        self.client = client or anthropic.AsyncAnthropic()
        self.results_path = config.results_dir / "results.jsonl"
        self.errors_path = config.results_dir / "errors.jsonl"
        self.traces_dir = config.results_dir / "traces"
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(config.concurrency)

    def completed(self) -> set[str]:
        if not self.results_path.exists():
            return set()
        done = set()
        for line in self.results_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done.add(trial_key(row["prompt_id"], row["requested_model"], row["rep"]))
        return done

    async def _write(self, path: Path, row: dict[str, Any]) -> None:
        async with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a") as handle:
                handle.write(json.dumps(row) + "\n")

    async def _call(self, spec: CaseSpec, model: str, attempt: Attempt) -> Any:
        delay = 1.0
        last: Exception | None = None
        for _ in range(self.config.max_attempts):
            try:
                async with self.client.messages.stream(
                    model=model,
                    max_tokens=self.config.max_tokens,
                    system=system_blocks(),
                    messages=[{"role": "user", "content": user_content(spec)}],
                    output_config={
                        "effort": self.config.effort,
                        "format": {
                            "type": "json_schema",
                            "schema": ExtractedSubmission.model_json_schema(),
                        },
                    },
                ) as stream:
                    return await stream.get_final_message()
            except RETRYABLE as error:
                last = error
                attempt.retries += 1
                await asyncio.sleep(delay + random.uniform(0, delay))
                delay = min(delay * 2, 30.0)
        raise last if last else RuntimeError("retry loop exhausted without an error")

    async def run_trial(self, spec: CaseSpec, model: str, rep: int) -> dict[str, Any] | None:
        case = spec.case
        attempt = Attempt()
        async with self._semaphore:
            try:
                response = await asyncio.wait_for(
                    self._call(spec, model, attempt), timeout=self.config.case_timeout_s
                )
            except TimeoutError:
                await self._error(case.case_id, model, rep, "timeout", attempt, None)
                return None
            except ValidationError as error:
                await self._error(case.case_id, model, rep, "unparseable", attempt, str(error))
                return None
            except anthropic.APIStatusError as error:
                await self._error(
                    case.case_id, model, rep, "api_error", attempt, f"{error.status_code}"
                )
                return None

        served = getattr(response, "model", "") or ""
        if not served.startswith(model):
            await self._error(
                case.case_id,
                model,
                rep,
                "served_model_mismatch",
                attempt,
                f"asked {model}, served {served}",
            )
            return None

        stop_reason = getattr(response, "stop_reason", None)
        usage = _usage_dict(response.usage)
        refused = stop_reason == "refusal"
        truncated = stop_reason == "max_tokens"

        if truncated:
            await self._error(
                case.case_id,
                model,
                rep,
                "truncated",
                attempt,
                f"hit max_tokens at {usage['output_tokens']} output tokens",
            )
            return None

        if refused:
            metrics = dict.fromkeys(_grade_metrics_keys(), 0.0)
            metrics["refused"] = 1.0
            status = "refusal"
            verdict = None
        else:
            body = "".join(block.text for block in response.content if block.type == "text")
            try:
                produced = ExtractedSubmission.model_validate_json(body)
            except ValidationError as error:
                await self._error(
                    case.case_id, model, rep, "unparseable", attempt, str(error)[:400]
                )
                return None
            verdict = grade(case, produced, packet_text=packet_text(spec))
            metrics = _grade_metrics(verdict)
            status = "ok"

        row = {
            "prompt_id": case.case_id,
            "prompt": prompt_text(spec),
            "tags": [case.kind, case.exercises.value if case.exercises else "none", model],
            "rep": rep,
            "requested_model": model,
            "model": served,
            "effort": self.config.effort,
            "stop_reason": stop_reason,
            "status": status,
            "grade": metrics,
            "usage": usage,
            "latency_s": round(attempt.elapsed, 2),
            "attempts": attempt.retries + 1,
            "meta": {
                "title": case.title,
                "paired_with": case.paired_with,
                "corruption": case.corruption,
                "declared_fields": list(case.should_flag_fields),
            },
        }
        if verdict is not None:
            row["verdict"] = verdict.model_dump(mode="json")

        self.traces_dir.mkdir(parents=True, exist_ok=True)
        trace_name = f"{case.case_id}_{model}_rep{rep}.json"
        (self.traces_dir / trace_name).write_text(
            json.dumps(_trace(spec, response), indent=2) + "\n"
        )
        await self._write(self.results_path, row)
        return row

    async def _error(
        self,
        case_id: str,
        model: str,
        rep: int,
        failure: str,
        attempt: Attempt,
        detail: str | None,
    ) -> None:
        await self._write(
            self.errors_path,
            {
                "prompt_id": case_id,
                "requested_model": model,
                "rep": rep,
                "failure": failure,
                "attempts": attempt.retries + 1,
                "latency_s": round(attempt.elapsed, 2),
                "detail": detail,
            },
        )

    async def run(self, specs: list[CaseSpec], *, force: bool = False) -> list[dict[str, Any]]:
        done = set() if force else self.completed()
        work = [
            (spec, model, rep)
            for spec in specs
            for model in self.config.models
            for rep in range(self.config.reps)
            if force or trial_key(spec.case.case_id, model, rep) not in done
        ]
        results = await asyncio.gather(
            *(self.run_trial(spec, model, rep) for spec, model, rep in work)
        )
        return [row for row in results if row is not None]


def _grade_metrics_keys() -> tuple[str, ...]:
    return (
        "case_passed",
        "value_score",
        "provenance_score",
        "correctly_flagged",
        "correctly_not_flagged",
        "missed_flag",
        "spurious_flag",
        "loss_arithmetic_ok",
        "locations_ok",
        "refused",
    )
