from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import FACEBOOK_EXTRACTION_ARTIFACTS_ROOT, RAW_WEEKLY_ROOT, STAGE_PYTHON
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


def _safe_csv_rows(path: Path) -> int | None:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def _build_commands(context: RadarRunContext) -> dict[str, list[str]]:
    start = context.selected_start_date.isoformat()
    end = context.selected_end_date.isoformat()
    _py = STAGE_PYTHON["extraction"]
    return {
        "facebook": [
            _py,
            "-m",
            "src.extraction.runners.facebook_extractor_apify_tampico",
            "--since",
            start,
            "--before",
            end,
            "--output-dir",
            str(FACEBOOK_EXTRACTION_ARTIFACTS_ROOT),
            "--publish-canonical",
            "--overwrite",
            "--no-prompt",
        ],
        "twitter": [
            _py,
            "-m",
            "src.extraction.runners.twitter_extractor_tampico",
            start,
            end,
        ],
        "youtube": [
            _py,
            "-m",
            "src.extraction.runners.youtube_extractor_tampico",
            "--since",
            start,
            "--before",
            end,
            "--output-dir",
            str(RAW_WEEKLY_ROOT),
        ],
        "medios": [
            _py,
            "-m",
            "src.extraction.runners.medios_extractor",
            "--since",
            start,
            "--before",
            end,
            "--output-dir",
            str(RAW_WEEKLY_ROOT),
        ],
    }


def _validate_outputs(context: RadarRunContext, source: str) -> dict[str, Any]:
    week_dir = RAW_WEEKLY_ROOT / context.week.folder_name
    if source == "facebook":
        artifact_dir = FACEBOOK_EXTRACTION_ARTIFACTS_ROOT / context.week.folder_name
        main_csv = artifact_dir / f"facebook_institutional_raw_{context.week.folder_name}.csv"
        return {
            "ok": artifact_dir.exists() and main_csv.exists(),
            "artifact_dir": str(artifact_dir),
            "main_csv": str(main_csv),
            "rows": _safe_csv_rows(main_csv) if main_csv.exists() else None,
        }

    expected = week_dir / f"{context.week.folder_name}_{source}.csv"
    payload = {
        "ok": expected.exists(),
        "path": str(expected),
        "rows": _safe_csv_rows(expected) if expected.exists() else None,
        "size_bytes": expected.stat().st_size if expected.exists() else None,
    }
    if source == "medios":
        txt_path = week_dir / f"{context.week.folder_name}_medios.txt"
        payload["txt_path"] = str(txt_path)
        payload["txt_exists"] = txt_path.exists()
        payload["txt_size_bytes"] = txt_path.stat().st_size if txt_path.exists() else None
        payload["ok"] = payload["ok"] and txt_path.exists()
    return payload


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    commands = _build_commands(context)
    inputs = {
        "week": context.week.to_dict(),
        "selection_window": context.selection_window_payload(),
        "sources": context.sources_effective,
    }
    outputs: dict[str, Any] = {"sources": {}}
    artifacts: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    command_payloads: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {"sources_total": len(context.sources_effective), "sources_ok": 0}

    if context.dry_run:
        for source in context.sources_effective:
            command_payloads.append(
                context.run_command("extraction", f"extract_{source}", commands[source], check=False)
            )
        finished_at = now_text()
        return StageResult(
            stage_name="extraction",
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={"planned_commands": command_payloads},
            artifacts=[],
            metrics=metrics,
            warnings=[],
            errors=[],
            notes=["Dry-run: se validó la planificación de comandos sin ejecutar extractores."],
            commands=command_payloads,
        )

    for source in context.sources_effective:
        payload = context.run_command("extraction", f"extract_{source}", commands[source], check=False)
        command_payloads.append(payload)
        validation = _validate_outputs(context, source)
        outputs["sources"][source] = validation

        if payload["returncode"] != 0:
            errors.append(f"{source}: el extractor terminó con código {payload['returncode']}.")
            continue
        if not validation["ok"]:
            errors.append(f"{source}: no se encontraron los artefactos esperados tras la extracción.")
            continue

        metrics["sources_ok"] += 1
        if source == "facebook":
            artifacts.append(validation["main_csv"])
        else:
            artifacts.append(validation["path"])
            if source == "medios":
                artifacts.append(validation["txt_path"])

    if errors and metrics["sources_ok"] == 0:
        status = "failed"
    elif errors:
        status = "partial_success"
        warnings.append("Al menos una fuente falló o dejó artefactos incompletos durante extracción.")
    else:
        status = "success"

    finished_at = now_text()
    return StageResult(
        stage_name="extraction",
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
        inputs=inputs,
        outputs=outputs,
        artifacts=artifacts,
        metrics=metrics,
        warnings=warnings,
        errors=errors,
        notes=[
            "Facebook publica artefactos canónicos semanales en artifacts/runs/extraction/facebook y se promueve en preprocessing."
        ],
        commands=command_payloads,
    )
