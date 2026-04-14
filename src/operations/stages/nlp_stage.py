from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import pandas as pd

from ..config import DEFAULT_MODEL_DATASET, PROCESSED_MODELING_ROOT, TEXT_WEEKLY_ROOT
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


SENTIMIENTO_OUTPUT = PROCESSED_MODELING_ROOT / "aceptacion_digital_redes_medios_sentimiento_semanal.xlsx"
MENSUAL_OUTPUT = PROCESSED_MODELING_ROOT / "encuestas_y_sentimiento_mensual_unificado.xlsx"
ML0_OUTPUT = PROCESSED_MODELING_ROOT / "datos_ml_0.xlsx"


def _validate_sentimiento_output(context: RadarRunContext) -> dict[str, Any]:
    if not SENTIMIENTO_OUTPUT.exists():
        return {"ok": False, "path": str(SENTIMIENTO_OUTPUT)}
    df = pd.read_excel(SENTIMIENTO_OUTPUT, sheet_name="sentimiento_semanal")
    week_present = bool((df["periodo_iso"] == context.week.slug).any()) if "periodo_iso" in df.columns else False
    return {
        "ok": week_present,
        "path": str(SENTIMIENTO_OUTPUT),
        "rows": len(df),
        "columns": list(df.columns),
        "week_present": week_present,
    }


def _validate_excel(path: Path, *, sheet_name: str | None = None) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "path": str(path)}
    df = pd.read_excel(path, sheet_name=sheet_name) if sheet_name else pd.read_excel(path)
    return {
        "ok": True,
        "path": str(path),
        "rows": len(df),
        "columns": list(df.columns),
    }


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    outputs: dict[str, Any] = {}
    artifacts: list[str] = []
    inputs = {
        "text_inputs": {
            source: str(TEXT_WEEKLY_ROOT / f"{source}_semana_texto" / f"{context.week.start_date.isoformat()}_{source}.txt")
            for source in context.sources_effective
        }
    }

    command_specs = [
        ("sentimiento_semanal", [sys.executable, "-m", "src.nlp.aceptacion_digital_redes_ponderacion_medios"]),
        ("encuestas_sentimiento", [sys.executable, "-m", "src.nlp.unificar_encuestas_sentimiento"]),
        ("dataset_ml_0", [sys.executable, "-m", "src.nlp.unir_ml_ready_con_sentimiento"]),
    ]

    if context.dry_run:
        for label, command in command_specs:
            commands.append(context.run_command("nlp", label, command, check=False))
        finished_at = now_text()
        return StageResult(
            stage_name="nlp",
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
            notes=["Dry-run: no se ejecutaron scripts NLP."],
            commands=commands,
        )

    for label, command in command_specs:
        commands.append(context.run_command("nlp", label, command))

    outputs["sentimiento_semanal"] = _validate_sentimiento_output(context)
    outputs["encuestas_sentimiento_mensual"] = _validate_excel(MENSUAL_OUTPUT, sheet_name="mensual_unificado")
    outputs["datos_ml_0"] = _validate_excel(ML0_OUTPUT, sheet_name="ML_Ready_Train")

    for key, payload in outputs.items():
        if payload.get("ok"):
            artifacts.append(payload["path"])
        else:
            errors.append(f"{key}: no se generó o no quedó validado el artefacto esperado.")

    if DEFAULT_MODEL_DATASET.exists():
        outputs["canonical_model_dataset"] = {
            "ok": True,
            "path": str(DEFAULT_MODEL_DATASET),
            "reused_existing_artifact": True,
        }
        artifacts.append(str(DEFAULT_MODEL_DATASET))
        warnings.append(
            "El dataset maestro de modelado se reutiliza como artefacto canónico existente; la capa NLP activa aún no lo recompone íntegramente."
        )
        status = "partial_success" if errors else "partial_success"
    else:
        outputs["canonical_model_dataset"] = {
            "ok": False,
            "path": str(DEFAULT_MODEL_DATASET),
            "reused_existing_artifact": False,
        }
        errors.append(
            "No existe el dataset maestro canónico consumido por modeling: datos_ml_master_indice_aceptacion_digital.xlsx."
        )
        status = "failed"

    if errors and len(errors) == len(outputs):
        status = "failed"
    elif errors and status != "failed":
        status = "partial_success"

    metrics = {
        "sentimiento_rows": outputs["sentimiento_semanal"].get("rows"),
        "ml0_rows": outputs["datos_ml_0"].get("rows"),
    }

    finished_at = now_text()
    return StageResult(
        stage_name="nlp",
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
            "La etapa NLP ejecuta solo scripts canónicos vigentes y deja explícito cuando reutiliza un dataset maestro ya existente."
        ],
        commands=commands,
    )
