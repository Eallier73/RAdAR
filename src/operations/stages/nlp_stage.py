from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import pandas as pd

from ..config import DEFAULT_MODEL_DATASET, PROCESSED_MODELING_ROOT, STAGE_PYTHON, TEXT_WEEKLY_ROOT
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text
from ...nlp.week_resolution import parse_week_token


SENTIMIENTO_OUTPUT = PROCESSED_MODELING_ROOT / "aceptacion_digital_redes_medios_sentimiento_semanal.xlsx"
MENSUAL_OUTPUT = PROCESSED_MODELING_ROOT / "encuestas_y_sentimiento_mensual_unificado.xlsx"
ML_READY_OUTPUT = PROCESSED_MODELING_ROOT / "ml_ready_monica_villarreal_encuestas_pmi_1.xlsx"
ML0_OUTPUT = PROCESSED_MODELING_ROOT / "datos_ml_0.xlsx"
PMI_RESULTS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "reference"
    / "dictionaries_nlp"
    / "resultados_clasificacion_temas"
)
PMI_CONSOLIDATED_OUTPUT = PMI_RESULTS_ROOT / "pmi_confianza_corpus_unido_consolidado.xlsx"
PMI_NORMALIZED_OUTPUT = PMI_RESULTS_ROOT / "pmi_confianza_corpus_unido_consolidado_normalizado.xlsx"
PMI_DICT_V5 = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "reference"
    / "dictionaries_nlp"
    / "diccionarios_finales"
    / "diccionario_pmi_confianza_v5.xlsx"
)
PMI_DICT_V10 = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "reference"
    / "dictionaries_nlp"
    / "diccionarios_finales"
    / "diccionario_pmi_confianza_v10.xlsx"
)


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


def _validate_ml_ready_output(context: RadarRunContext) -> dict[str, Any]:
    if not ML_READY_OUTPUT.exists():
        return {"ok": False, "path": str(ML_READY_OUTPUT)}

    df = pd.read_excel(ML_READY_OUTPUT, sheet_name="ML_Ready_AllWeeks")
    if "semana_iso" not in df.columns:
        return {"ok": False, "path": str(ML_READY_OUTPUT), "rows": len(df), "columns": list(df.columns)}

    week_mask = df["semana_iso"].astype(str) == context.week.slug
    week_present = bool(week_mask.any())
    has_full_pmi = False
    if week_present and "has_full_pmi_features" in df.columns:
        row = df.loc[week_mask].iloc[-1]
        has_full_pmi = bool(int(row["has_full_pmi_features"]) == 1)

    return {
        "ok": week_present and has_full_pmi,
        "path": str(ML_READY_OUTPUT),
        "rows": len(df),
        "columns": list(df.columns),
        "week_present": week_present,
        "has_full_pmi_features": has_full_pmi,
    }


def _validate_ml0_output(context: RadarRunContext) -> dict[str, Any]:
    if not ML0_OUTPUT.exists():
        return {"ok": False, "path": str(ML0_OUTPUT)}

    df = pd.read_excel(ML0_OUTPUT, sheet_name="ML_Ready_AllWeeks")
    if "semana_iso" not in df.columns:
        return {"ok": False, "path": str(ML0_OUTPUT), "rows": len(df), "columns": list(df.columns)}

    week_mask = df["semana_iso"].astype(str) == context.week.slug
    week_present = bool(week_mask.any())
    has_full_pmi = False
    has_sentiment = False
    if week_present:
        row = df.loc[week_mask].iloc[-1]
        if "has_full_pmi_features" in df.columns:
            has_full_pmi = bool(int(row["has_full_pmi_features"]) == 1)
        if "flag_missing_sentimiento_digital" in df.columns:
            has_sentiment = bool(int(row["flag_missing_sentimiento_digital"]) == 0)

    return {
        "ok": week_present and has_full_pmi and has_sentiment,
        "path": str(ML0_OUTPUT),
        "rows": len(df),
        "columns": list(df.columns),
        "week_present": week_present,
        "has_full_pmi_features": has_full_pmi,
        "has_sentiment": has_sentiment,
    }


def _validate_pmi_normalized_output(context: RadarRunContext) -> dict[str, Any]:
    if not PMI_NORMALIZED_OUTPUT.exists():
        return {"ok": False, "path": str(PMI_NORMALIZED_OUTPUT)}

    df = pd.read_excel(PMI_NORMALIZED_OUTPUT, sheet_name="Consolidado_V5")
    week_present = False
    if not df.empty:
        values = df.iloc[:, 0].astype(str).tolist()
        for value in values:
            if value.upper() == "TOTAL":
                continue
            try:
                start_date = parse_week_token(value)
            except ValueError:
                continue
            if start_date == context.week.start_date:
                week_present = True
                break

    return {
        "ok": week_present,
        "path": str(PMI_NORMALIZED_OUTPUT),
        "rows": len(df),
        "columns": list(df.columns),
        "week_present": week_present,
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
        "selection_window": context.selection_window_payload(),
        "sources": list(context.sources_effective),
        "text_inputs": {
            source: str(TEXT_WEEKLY_ROOT / f"{source}_semana_texto" / f"{context.week.start_date.isoformat()}_{source}.txt")
            for source in context.sources_effective
        }
    }

    _py = STAGE_PYTHON["nlp"]
    sentimiento_command = [
        _py,
        "-m",
        "src.nlp.aceptacion_digital_redes_ponderacion_medios",
        "--sources",
        *context.sources_effective,
        "--week",
        context.week.slug,
        "--date-from",
        context.selected_start_date.isoformat(),
        "--date-to",
        context.selected_end_date.isoformat(),
    ]
    command_specs = [
        ("sentimiento_semanal", sentimiento_command),
        ("encuestas_sentimiento", [_py, "-m", "src.nlp.unificar_encuestas_sentimiento"]),
        (
            "clasificacion_temas_pmi_confianza",
            [
                _py,
                "-m",
                "src.nlp.clasificacion_temas_pmi_confianza",
                "--dict_v5",
                str(PMI_DICT_V5),
                "--dict_v10",
                str(PMI_DICT_V10),
                "--output",
                str(PMI_RESULTS_ROOT),
                "--nombre",
                "pmi_confianza_corpus_unido",
                "--datos",
                str(TEXT_WEEKLY_ROOT),
                "--through-date",
                context.selected_end_date.isoformat(),
            ],
        ),
        (
            "normalizacion_temas_pmi_confianza",
            [
                _py,
                "-m",
                "src.nlp.resultados_clasificacion_temas_pmi_confianza_normalizado",
                "--input",
                str(PMI_CONSOLIDATED_OUTPUT),
                "--output",
                str(PMI_NORMALIZED_OUTPUT),
            ],
        ),
        (
            "ml_ready_encuestas_pmi",
            [
                _py,
                "-m",
                "src.nlp.generar_ml_ready_encuestas_pmi",
                "--scaffold",
                str(ML_READY_OUTPUT),
                "--pmi-normalized",
                str(PMI_NORMALIZED_OUTPUT),
                "--output",
                str(ML_READY_OUTPUT),
                "--through-date",
                context.selected_end_date.isoformat(),
            ],
        ),
        ("dataset_ml_0", [_py, "-m", "src.nlp.unir_ml_ready_con_sentimiento"]),
        (
            "canonical_model_dataset",
            [
                _py,
                "-m",
                "src.nlp.reconstruir_dataset_aceptacion_digital",
                "--input-ml0",
                str(ML0_OUTPUT),
                "--output-dir",
                str(PROCESSED_MODELING_ROOT),
            ],
        ),
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
    outputs["pmi_normalizado"] = _validate_pmi_normalized_output(context)
    outputs["ml_ready_encuestas_pmi"] = _validate_ml_ready_output(context)
    outputs["datos_ml_0"] = _validate_ml0_output(context)
    outputs["canonical_model_dataset"] = _validate_excel(DEFAULT_MODEL_DATASET)

    for key, payload in outputs.items():
        if payload.get("ok"):
            artifacts.append(payload["path"])
        else:
            errors.append(f"{key}: no se generó o no quedó validado el artefacto esperado.")

    warnings.append(
        "La etapa NLP operativa ya ejecuta sentimiento, clasificacion PMI, normalizacion, "
        "refresco de ML-ready y reconstruccion del dataset maestro. "
        "Si la corrida rebasa el horizonte del scaffold semanal de encuestas, el ML-ready se extiende por carry-forward."
    )

    if errors and len(errors) == len(outputs):
        status = "failed"
    elif errors:
        status = "partial_success"
    else:
        status = "success"

    metrics = {
        "sentimiento_rows": outputs["sentimiento_semanal"].get("rows"),
        "pmi_normalizado_rows": outputs["pmi_normalizado"].get("rows"),
        "ml_ready_rows": outputs["ml_ready_encuestas_pmi"].get("rows"),
        "ml0_rows": outputs["datos_ml_0"].get("rows"),
        "canonical_model_dataset_rows": outputs["canonical_model_dataset"].get("rows"),
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
            "La etapa NLP ejecuta sentimiento, PMI, union ML-ready y reconstruccion final del dataset canonico."
        ],
        commands=commands,
    )
