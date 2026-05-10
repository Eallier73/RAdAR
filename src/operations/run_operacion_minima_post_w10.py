from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DEFAULT_SOURCES, EXPERIMENTS_RUNS_DIR, MODELING_PYTHON, OPERATIONS_ARTIFACTS_ROOT, OPS_PYTHON
from .frozen_profiles import (
    CONTROLLED_OPERATION_START,
    CONTROLLED_OPERATION_START_WEEK,
    DEFAULT_OPERATION_DATASET,
    E9_CURATED_TABLE_PATH,
    NUMERIC_PRIMARY_RUN_ID,
    PRIMARY_OPERATION_RUN_IDS,
    RISK_PRIMARY_RUN_ID,
    iter_week_starts,
    latest_common_text_week_start,
    load_all_operation_profiles,
    week_slug,
)
from .run_context import build_repo_context_snapshot, now_text, resolve_week_window


PIPELINE_PROFILE_ID = "radar_controlled_post_w10_v1"
OPERATION_STAGE_ORDER = ("extraction", "preprocessing", "nlp", "modeling")
WEEKLY_PIPELINE_STAGE_ORDER = ("extraction", "preprocessing", "nlp")


@dataclass
class ExecutedCommand:
    label: str
    command: list[str]
    returncode: int
    started_at: str
    finished_at: str
    run_dir: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Puesta en operacion minima controlada post-W10. "
            "Orquesta backfill NLP, refresco de perfiles congelados y registro formal de emisiones."
        )
    )
    parser.add_argument("--from-week", default=CONTROLLED_OPERATION_START_WEEK)
    parser.add_argument("--to-week", help="Default: ultima semana canónica común disponible en data/text.")
    parser.add_argument(
        "--pipeline-from-stage",
        choices=OPERATION_STAGE_ORDER,
        default="extraction",
        help="Etapa inicial de la operación post-W10. Default: extraction.",
    )
    parser.add_argument(
        "--pipeline-to-stage",
        choices=OPERATION_STAGE_ORDER,
        default="modeling",
        help="Etapa final de la operación post-W10. Default: modeling.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--comment", default="")
    parser.add_argument("--operation-id", help="Identificador explicito para la corrida operativa.")
    parser.add_argument("--ops-python", default=OPS_PYTHON)
    parser.add_argument("--modeling-python", default=MODELING_PYTHON)
    parser.add_argument("--fail-fast", dest="fail_fast", action="store_true", default=True)
    parser.add_argument("--no-fail-fast", dest="fail_fast", action="store_false")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=list(DEFAULT_SOURCES),
        choices=list(DEFAULT_SOURCES),
        help="Fuentes para el backfill NLP. Default: todas.",
    )
    return parser.parse_args(argv)


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _operation_id(explicit: str | None) -> str:
    return explicit or f"post_w10_{_now_stamp()}"


def _ensure_dirs(root: Path) -> dict[str, Path]:
    paths = {
        "root": root,
        "logs": root / "logs",
        "emisiones": root / "emisiones",
        "snapshots": root / "snapshots",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def _emit(log_path: Path, message: str) -> None:
    line = f"[{now_text()}] {message}"
    print(line, flush=True)
    _append_log(log_path, line)


def _discover_new_run_dir(prefix: str, before: set[Path], after: set[Path]) -> Path | None:
    created = sorted(after - before)
    if created:
        return created[-1]
    candidates = sorted(EXPERIMENTS_RUNS_DIR.glob(f"{prefix}_*"))
    return candidates[-1] if candidates else None


def _run_command(
    *,
    label: str,
    command: list[str],
    log_path: Path,
    dry_run: bool,
    fail_fast: bool,
    discover_prefix: str | None = None,
) -> ExecutedCommand:
    started_at = now_text()
    _emit(log_path, f"{label}: {shlex.join(command)}")
    if dry_run:
        return ExecutedCommand(
            label=label,
            command=command,
            returncode=0,
            started_at=started_at,
            finished_at=now_text(),
            run_dir=None,
        )

    before = set()
    if discover_prefix:
        before = set(EXPERIMENTS_RUNS_DIR.glob(f"{discover_prefix}_*"))

    process = subprocess.Popen(
        command,
        cwd=str(Path(__file__).resolve().parents[2]),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        _append_log(log_path, line.rstrip("\n"))
    process.stdout.close()
    returncode = process.wait()
    finished_at = now_text()
    run_dir = None
    if discover_prefix:
        after = set(EXPERIMENTS_RUNS_DIR.glob(f"{discover_prefix}_*"))
        discovered = _discover_new_run_dir(discover_prefix, before, after)
        run_dir = str(discovered) if discovered else None
    if returncode != 0 and fail_fast:
        raise subprocess.CalledProcessError(returncode, command)
    return ExecutedCommand(
        label=label,
        command=command,
        returncode=returncode,
        started_at=started_at,
        finished_at=finished_at,
        run_dir=run_dir,
    )


def _pipeline_command(
    *,
    ops_python: str,
    week: str,
    from_stage: str,
    to_stage: str,
    sources: list[str],
) -> list[str]:
    command = [
        ops_python,
        "-m",
        "src.operations.run_radar_pipeline",
        "--week",
        week,
        "--mode",
        "controlled",
        "--from-stage",
        from_stage,
        "--to-stage",
        to_stage,
        "--sources",
        *sources,
    ]
    return command


def _runtime_run_id(operation_id: str, canonical_run_id: str) -> str:
    return f"{operation_id}_{canonical_run_id}"


def _stage_index(stage_name: str, order: tuple[str, ...]) -> int:
    return order.index(stage_name)


def _validate_operation_stage_bounds(from_stage: str, to_stage: str) -> None:
    if _stage_index(from_stage, OPERATION_STAGE_ORDER) > _stage_index(to_stage, OPERATION_STAGE_ORDER):
        raise ValueError("--pipeline-from-stage no puede ir después de --pipeline-to-stage.")


def _resolve_weekly_pipeline_bounds(from_stage: str, to_stage: str) -> tuple[str, str] | None:
    if from_stage == "modeling":
        return None
    weekly_to = to_stage if to_stage in WEEKLY_PIPELINE_STAGE_ORDER else "nlp"
    return from_stage, weekly_to


def _emission_builder_command(
    *,
    modeling_python: str,
    operation_id: str,
    operation_root: Path,
    from_week: str,
    to_week: str,
    comment: str,
    refreshed_run_dirs: dict[str, str],
) -> list[str]:
    return [
        modeling_python,
        "-m",
        "src.operations.build_emission_registry_post_w10",
        "--operation-id",
        operation_id,
        "--operation-root",
        str(operation_root),
        "--from-week",
        from_week,
        "--to-week",
        to_week,
        "--dataset-path",
        str(DEFAULT_OPERATION_DATASET),
        "--comment",
        comment,
        "--e1-run-dir",
        refreshed_run_dirs[NUMERIC_PRIMARY_RUN_ID],
        "--e9-run-dir",
        refreshed_run_dirs[RISK_PRIMARY_RUN_ID],
    ]


def _canonical_profiles_payload(profiles: dict[str, Any]) -> dict[str, dict[str, str]]:
    payload: dict[str, dict[str, str]] = {}
    for run_id, profile in profiles.items():
        payload[run_id] = {
            "role": profile.role,
            "canonical_run_dir": str(profile.canonical_run_dir),
            "metadata_path": str(profile.metadata_path),
            "parameters_path": str(profile.parameters_path),
            "runner_module": profile.runner_module,
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _validate_operation_stage_bounds(args.pipeline_from_stage, args.pipeline_to_stage)
    profiles = load_all_operation_profiles()
    repo_context = build_repo_context_snapshot()
    latest_text_week = latest_common_text_week_start()
    start_week = resolve_week_window(args.from_week).start_date
    end_week = resolve_week_window(args.to_week).start_date if args.to_week else latest_text_week
    if end_week < start_week:
        raise ValueError("--to-week no puede ser anterior a --from-week.")

    operation_id = _operation_id(args.operation_id)
    operation_root = OPERATIONS_ARTIFACTS_ROOT / "post_w10" / operation_id
    paths = _ensure_dirs(operation_root)
    log_path = paths["logs"] / "operacion.log"
    operation_payload = {
        "operation_id": operation_id,
        "started_at": now_text(),
        "operation_profile_id": PIPELINE_PROFILE_ID,
        "operation_mode": "predict_only_frozen_inference",
        "validated_history_last_week": "2026-W10",
        "validated_history_last_start": "2026-03-02",
        "operation_start_week": CONTROLLED_OPERATION_START_WEEK,
        "from_week": week_slug(start_week),
        "to_week": week_slug(end_week),
        "latest_common_text_week": week_slug(latest_text_week),
        "pipeline_from_stage": args.pipeline_from_stage,
        "pipeline_to_stage": args.pipeline_to_stage,
        "dataset_path": str(DEFAULT_OPERATION_DATASET),
        "e9_curated_table_path": str(E9_CURATED_TABLE_PATH),
        "ops_python": args.ops_python,
        "modeling_python": args.modeling_python,
        "primary_profiles": list(PRIMARY_OPERATION_RUN_IDS),
        "canonical_profiles": _canonical_profiles_payload(profiles),
        "repo_context": repo_context,
        "comment": args.comment,
        "dry_run": args.dry_run,
    }
    (operation_root / "manifest.json").write_text(
        json.dumps(operation_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    week_sequence = iter_week_starts(start_week, end_week)
    commands_executed: list[ExecutedCommand] = []
    weekly_bounds = _resolve_weekly_pipeline_bounds(args.pipeline_from_stage, args.pipeline_to_stage)
    if weekly_bounds is not None:
        weekly_from_stage, weekly_to_stage = weekly_bounds
        for week_start in week_sequence:
            slug = week_slug(week_start)
            commands_executed.append(
                _run_command(
                    label=f"pipeline_{weekly_from_stage}_{weekly_to_stage}_{slug}",
                    command=_pipeline_command(
                        ops_python=args.ops_python,
                        week=slug,
                        from_stage=weekly_from_stage,
                        to_stage=weekly_to_stage,
                        sources=list(args.sources),
                    ),
                    log_path=log_path,
                    dry_run=args.dry_run,
                    fail_fast=args.fail_fast,
                )
            )

    should_run_modeling = args.pipeline_to_stage == "modeling"
    if not should_run_modeling:
        if args.dry_run:
            (operation_root / "plan_commands.json").write_text(
                json.dumps([asdict(item) for item in commands_executed], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _emit(log_path, "Dry-run completado. No se materializaron emisiones.")
            return 0
        summary_path = operation_root / "summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "operation_id": operation_id,
                    "finished_at": now_text(),
                    "refreshed_run_dirs": {},
                    "commands_executed": [asdict(item) for item in commands_executed],
                    "notes": ["La operación se cerró antes de modeling por selección explícita de etapas."],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        _emit(log_path, f"Operacion completada sin modelado. Summary: {summary_path}")
        return 0

    if args.dry_run:
        (operation_root / "plan_commands.json").write_text(
            json.dumps([asdict(item) for item in commands_executed], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _emit(log_path, "Dry-run completado. No se materializaron emisiones.")
        return 0

    emission_result = _run_command(
        label="build_emission_registry",
        command=_emission_builder_command(
            modeling_python=args.modeling_python,
            operation_id=operation_id,
            operation_root=operation_root,
            from_week=week_slug(start_week),
            to_week=week_slug(end_week),
            comment=args.comment,
            refreshed_run_dirs={
                NUMERIC_PRIMARY_RUN_ID: str(profiles[NUMERIC_PRIMARY_RUN_ID].canonical_run_dir),
                RISK_PRIMARY_RUN_ID: str(profiles[RISK_PRIMARY_RUN_ID].canonical_run_dir),
            },
        ),
        log_path=log_path,
        dry_run=False,
        fail_fast=args.fail_fast,
    )
    commands_executed.append(emission_result)
    summary_path = operation_root / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "operation_id": operation_id,
                "finished_at": now_text(),
                "refreshed_run_dirs": {},
                "predict_only_run_dirs": {
                    NUMERIC_PRIMARY_RUN_ID: str(profiles[NUMERIC_PRIMARY_RUN_ID].canonical_run_dir),
                    RISK_PRIMARY_RUN_ID: str(profiles[RISK_PRIMARY_RUN_ID].canonical_run_dir),
                },
                "commands_executed": [asdict(item) for item in commands_executed],
                "notes": [
                    "No se ejecutó refresh experimental de runs.",
                    "La etapa modeling de post_w10_controlled delegó únicamente a la ruta predict-only.",
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _emit(log_path, f"Operacion completada. Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
