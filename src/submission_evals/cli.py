from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer

from submission_evals.baselines import BASELINES
from submission_evals.cases import all_specs, spec_by_id
from submission_evals.generate import packet_text, write_all
from submission_evals.grade import grade
from submission_evals.runner import RunConfig, Runner


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


app = typer.Typer(add_completion=False, help="Grade an agent on commercial insurance intake.")

MODEL_OPTION = typer.Option(None, "--model", "-m")


def _specs(case: str | None):
    return [spec_by_id(case)] if case else all_specs()


@app.command()
def generate(out: Path = Path("packets")) -> None:
    paths = write_all(all_specs(), out)
    for path in paths:
        typer.echo(f"{path}  ({len(list(path.iterdir()))} files)")


@app.command()
def baseline(case: str | None = None) -> None:
    specs = _specs(case)
    header = f"{'case':<40}" + "".join(f"{name:>18}" for name in BASELINES)
    typer.echo(header)
    typer.echo("-" * len(header))
    for spec in specs:
        cells = []
        for build in BASELINES.values():
            verdict = grade(spec.case, build(spec.case), packet_text=packet_text(spec))
            mark = "pass" if verdict.case_passed else "FAIL"
            cells.append(f"{mark} v{verdict.value_score:.2f} p{verdict.provenance_score:.2f}")
        typer.echo(f"{spec.case.case_id:<40}" + "".join(f"{cell:>18}" for cell in cells))
    typer.echo("")
    typer.echo("oracle must pass everywhere; the other three must never pass.")


@app.command()
def cases() -> None:
    for spec in all_specs():
        case = spec.case
        flags = ", ".join(case.should_flag_fields) or "-"
        typer.echo(f"{case.case_id:<40} {case.kind:<12} flags: {flags}")
        typer.echo(f"{'':<40} {case.title}")


@app.command()
def run(
    case: str | None = None,
    model: list[str] = MODEL_OPTION,
    reps: int = 3,
    effort: str = "medium",
    concurrency: int = 6,
    results: Path = Path("results"),
    force: bool = False,
) -> None:
    load_env()
    config = RunConfig(
        models=tuple(model) if model else RunConfig.models,
        reps=reps,
        effort=effort,
        concurrency=concurrency,
        results_dir=results,
    )
    specs = _specs(case)
    planned = len(specs) * len(config.models) * config.reps
    runner = Runner(config)
    already = len(runner.completed())
    typer.echo(
        f"{len(specs)} cases x {len(config.models)} models x {reps} reps = {planned} trials "
        f"at effort {effort} ({already} already recorded)"
    )
    rows = asyncio.run(runner.run(specs, force=force))
    typer.echo(f"{len(rows)} trials recorded in {config.results_dir}")
    for row in rows:
        verdict = "pass" if row["grade"]["case_passed"] else "FAIL"
        typer.echo(
            f"  {row['prompt_id']:<40} {row['requested_model']:<20} rep{row['rep']} "
            f"{verdict}  value {row['grade']['value_score']:.2f} "
            f"prov {row['grade']['provenance_score']:.2f} "
            f"spurious {int(row['grade']['spurious_flag'])}"
        )


@app.command()
def show(case: str, document: str | None = None) -> None:
    spec = spec_by_id(case)
    text = packet_text(spec)
    for name, body in text.items():
        if document and name.value != document:
            continue
        typer.echo(f"===== {name.value} =====")
        typer.echo(body)


@app.command()
def summarise(results: Path = Path("results")) -> None:
    path = results / "results.jsonl"
    if not path.exists():
        typer.echo(f"no results at {path}")
        raise typer.Exit(1)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    by_case: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        by_case.setdefault((row["prompt_id"], row["requested_model"]), []).append(row)
    typer.echo(f"{'case':<40}{'model':<22}{'passed':>10}")
    typer.echo("-" * 72)
    for (case_id, model), group in sorted(by_case.items()):
        passed = sum(int(row["grade"]["case_passed"]) for row in group)
        typer.echo(f"{case_id:<40}{model:<22}{passed:>5}/{len(group)}")


if __name__ == "__main__":
    app()
