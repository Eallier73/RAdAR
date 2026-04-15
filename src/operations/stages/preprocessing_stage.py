from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import FACEBOOK_EXTRACTION_ARTIFACTS_ROOT, PREPROCESSING_REPORT_PATH, RAW_WEEKLY_ROOT, TEXT_WEEKLY_ROOT
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


def _count_csv_rows(path: Path) -> int | None:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def _text_output_path(context: RadarRunContext, source: str) -> Path:
    return TEXT_WEEKLY_ROOT / f"{source}_semana_texto" / f"{context.week.start_date.isoformat()}_{source}.txt"


def _validate_source_outputs(context: RadarRunContext, source: str) -> dict[str, Any]:
    week_dir = RAW_WEEKLY_ROOT / context.week.folder_name
    if source == "medios":
        raw_paths = {
            "raw_csv": week_dir / f"{context.week.folder_name}_medios.csv",
            "raw_txt": week_dir / f"{context.week.folder_name}_medios.txt",
            "text_txt": _text_output_path(context, source),
        }
        return {
            "ok": all(path.exists() for path in raw_paths.values()),
            "paths": {key: str(path) for key, path in raw_paths.items()},
            "raw_csv_rows": _count_csv_rows(raw_paths["raw_csv"]) if raw_paths["raw_csv"].exists() else None,
            "text_size_bytes": raw_paths["text_txt"].stat().st_size if raw_paths["text_txt"].exists() else None,
        }

    raw_csv = week_dir / f"{context.week.folder_name}_{source}.csv"
    text_txt = _text_output_path(context, source)
    return {
        "ok": raw_csv.exists() and text_txt.exists(),
        "paths": {
            "raw_csv": str(raw_csv),
            "text_txt": str(text_txt),
        },
        "raw_csv_rows": _count_csv_rows(raw_csv) if raw_csv.exists() else None,
        "text_size_bytes": text_txt.stat().st_size if text_txt.exists() else None,
    }


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    outputs: dict[str, Any] = {"sources": {}}
    artifacts: list[str] = []
    inputs = {
        "week_folder": str(RAW_WEEKLY_ROOT / context.week.folder_name),
        "selection_window": context.selection_window_payload(),
        "sources": context.sources_effective,
    }

    normalizar_cmd = [
        sys.executable,
        "-m",
        "src.preprocessing",
        "normalizar-semanas",
        "--raw-root",
        str(RAW_WEEKLY_ROOT),
        "--report",
        str(PREPROCESSING_REPORT_PATH),
        "--apply",
    ]
    promover_cmd = [
        sys.executable,
        "-m",
        "src.preprocessing",
        "promover-texto",
        "--apply",
    ]

    if context.dry_run:
        commands.append(context.run_command("preprocessing", "normalizar_semanas", normalizar_cmd, check=False))
        artifact_dir = FACEBOOK_EXTRACTION_ARTIFACTS_ROOT / context.week.folder_name
        if "facebook" in context.sources_effective:
            distribuir_cmd = [
                sys.executable,
                "-m",
                "src.preprocessing",
                "distribuir-facebook",
                "--src",
                str(artifact_dir),
                "--dest",
                str(RAW_WEEKLY_ROOT),
                "--apply",
            ]
            commands.append(context.run_command("preprocessing", "distribuir_facebook", distribuir_cmd, check=False))
        commands.append(context.run_command("preprocessing", "promover_texto", promover_cmd, check=False))
        finished_at = now_text()
        return StageResult(
            stage_name="preprocessing",
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={"planned_commands": commands},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[],
            notes=["Dry-run: no se materializaron cambios en data/raw ni data/text."],
            commands=commands,
        )

    commands.append(context.run_command("preprocessing", "normalizar_semanas", normalizar_cmd))

    artifact_dir = FACEBOOK_EXTRACTION_ARTIFACTS_ROOT / context.week.folder_name
    if "facebook" in context.sources_effective:
        if artifact_dir.exists():
            distribuir_cmd = [
                sys.executable,
                "-m",
                "src.preprocessing",
                "distribuir-facebook",
                "--src",
                str(artifact_dir),
                "--dest",
                str(RAW_WEEKLY_ROOT),
                "--apply",
            ]
            commands.append(context.run_command("preprocessing", "distribuir_facebook", distribuir_cmd))
        else:
            warnings.append(
                f"No existe directorio de artefactos intermedios de Facebook para esta semana: {artifact_dir}"
            )

    commands.append(context.run_command("preprocessing", "promover_texto", promover_cmd))

    metrics = {"sources_ok": 0, "sources_total": len(context.sources_effective)}
    for source in context.sources_effective:
        validation = _validate_source_outputs(context, source)
        outputs["sources"][source] = validation
        if validation["ok"]:
            metrics["sources_ok"] += 1
            artifacts.extend(validation["paths"].values())
        else:
            errors.append(f"{source}: faltan outputs canónicos en raw/text después de preprocessing.")

    report_path = PREPROCESSING_REPORT_PATH
    if report_path.exists():
        artifacts.append(str(report_path))

    if errors and metrics["sources_ok"] == 0:
        status = "failed"
    elif errors:
        status = "partial_success"
    else:
        status = "success"

    finished_at = now_text()
    return StageResult(
        stage_name="preprocessing",
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
        notes=["Esta etapa normaliza el raw semanal y promueve corpus de texto canónicos por fuente."],
        commands=commands,
    )
