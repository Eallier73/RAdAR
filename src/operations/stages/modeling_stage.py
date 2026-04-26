from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any

from ..config import DEFAULT_MODEL_DATASET, DEFAULT_MODEL_RUNNER, EXPERIMENTS_RUNS_DIR, EXPERIMENTS_WORKBOOK, STAGE_PYTHON
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


DATASET_OPTIONAL_RUNNERS = {
    "src.modeling.runners.run_e10_meta_selector",
}


def _discover_new_run_dir(prefix: str, before: set[Path], after: set[Path]) -> Path | None:
    new_candidates = sorted(after - before)
    if new_candidates:
        return new_candidates[-1]
    prefix_candidates = sorted(EXPERIMENTS_RUNS_DIR.glob(f"{prefix}_*"))
    return prefix_candidates[-1] if prefix_candidates else None


def _validate_model_run_dir(run_dir: Path | None) -> dict[str, Any]:
    if run_dir is None or not run_dir.exists():
        return {"ok": False, "run_dir": str(run_dir) if run_dir else ""}
    predictions = sorted(run_dir.glob("predicciones_h*.csv"))
    summary_json = run_dir / "resumen_modeling_horizontes.json"
    metadata_json = run_dir / "metadata_run.json"
    parametros_json = run_dir / "parametros_run.json"
    return {
        "ok": bool(predictions) and summary_json.exists() and metadata_json.exists() and parametros_json.exists(),
        "run_dir": str(run_dir),
        "predictions": [str(path) for path in predictions],
        "summary_json": str(summary_json),
        "metadata_json": str(metadata_json),
        "parametros_json": str(parametros_json),
    }


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    warnings: list[str] = []
    errors: list[str] = []
    commands: list[dict[str, Any]] = []
    artifacts: list[str] = []

    model_runner = context.metadata.get("model_runner", DEFAULT_MODEL_RUNNER)
    model_run_id = context.metadata.get("model_run_id") or f"{context.run_id}_model"
    extra_model_args = list(context.metadata.get("model_args", []))
    dataset_path = Path(context.metadata.get("model_dataset_path", DEFAULT_MODEL_DATASET))

    inputs = {
        "dataset_path": str(dataset_path),
        "model_runner": model_runner,
        "model_run_id": model_run_id,
        "model_args": extra_model_args,
    }

    command = [
        STAGE_PYTHON["modeling"],
        "-m",
        model_runner,
        "--run-id",
        model_run_id,
        "--workbook",
        str(EXPERIMENTS_WORKBOOK),
        "--runs-dir",
        str(EXPERIMENTS_RUNS_DIR),
    ]

    if model_runner not in DATASET_OPTIONAL_RUNNERS:
        command.extend(["--dataset-path", str(dataset_path)])
    command.extend(extra_model_args)

    if context.dry_run:
        commands.append(context.run_command("modeling", "run_model", command, check=False))
        finished_at = now_text()
        return StageResult(
            stage_name="modeling",
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
            notes=["Dry-run: no se lanzó el runner de modelado."],
            commands=commands,
        )

    if not dataset_path.exists():
        finished_at = now_text()
        return StageResult(
            stage_name="modeling",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[f"No existe el dataset maestro requerido para modelado: {dataset_path}"],
            notes=[],
            commands=[],
        )

    before = set(EXPERIMENTS_RUNS_DIR.glob(f"{model_run_id}_*"))
    command_payload = context.run_command("modeling", "run_model", command, check=False)
    commands.append(command_payload)
    if command_payload["returncode"] != 0:
        finished_at = now_text()
        return StageResult(
            stage_name="modeling",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[
                "El runner de modelado devolvió código distinto de cero. Revisa logs/modeling.log para stderr detallado.",
                f"returncode={command_payload['returncode']}",
            ],
            notes=["La etapa conserva el comando ejecutado y delega el detalle del traceback al log de etapa."],
            commands=commands,
        )

    after = set(EXPERIMENTS_RUNS_DIR.glob(f"{model_run_id}_*"))
    run_dir = _discover_new_run_dir(model_run_id, before, after)

    validation = _validate_model_run_dir(run_dir)
    if not validation["ok"]:
        errors.append("El runner de modelado terminó pero no dejó el set mínimo de artefactos esperados.")
        status = "failed"
    else:
        artifacts.extend(validation["predictions"])
        artifacts.extend(
            [
                validation["summary_json"],
                validation["metadata_json"],
                validation["parametros_json"],
            ]
        )
        status = "success"

    outputs = {
        "model_run_dir": validation.get("run_dir"),
        "model_run_id": model_run_id,
        "validation": validation,
    }
    metrics = {"prediction_files": len(validation.get("predictions", []))}
    if status == "success":
        warnings.append("El modelado operativo reutiliza el tracker experimental existente; no crea una capa paralela de tracking.")

    finished_at = now_text()
    return StageResult(
        stage_name="modeling",
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
        notes=["Esta etapa ejecuta solo runners canónicos y deja referencia directa al run registrado en experiments/runs."],
        commands=commands,
    )
