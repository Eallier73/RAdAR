from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import DEFAULT_MODEL_DATASET, ROOT_DIR, STAGE_PYTHON
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text
from ...modeling.selector.numeric_selector import (
    SelectorConfig,
    run_selector_analysis,
    format_results as format_selector_results,
)


EXPERIMENTS_RUNS_DIR = ROOT_DIR / "experiments" / "runs"

E9_CANDIDATES_BY_HORIZON: dict[int, tuple[str, ...]] = {
    1: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
    2: ("E1_v5_clean", "E5_v4_clean", "E2_v3_clean", "E7_v3_clean"),
    3: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E7_v3_clean"),
    4: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
}

FROZEN_BASE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "run_id": "E1_v5_clean",
        "module": "src.modeling.runners.run_e1_ridge_clean",
        "args": [
            "--run-id", "E1_v5_clean",
            "--reference-run-id", "E1_v5_clean",
            "--target-mode", "nivel",
            "--feature-mode", "corr",
            "--lags", "1,2,3,4,5,6",
            "--transform-mode", "standard",
            "--initial-train-size", "40",
            "--horizons", "1,2,3,4",
        ],
    },
    {
        "run_id": "E2_v3_clean",
        "module": "src.modeling.runners.run_e2_huber_clean",
        "args": [
            "--run-id", "E2_v3_clean",
            "--target-mode", "nivel",
            "--feature-mode", "corr",
            "--lags", "1,2,3,4",
            "--transform-mode", "standard",
            "--initial-train-size", "40",
            "--horizons", "1,2,3,4",
            "--hypothesis-note", "prueba_sin_memoria_larga",
        ],
    },
    {
        "run_id": "E3_v2_clean",
        "module": "src.modeling.runners.run_e3_random_forest",
        "args": [
            "--run-id", "E3_v2_clean",
            "--target-mode", "nivel",
            "--feature-mode", "all",
            "--lags", "1,2,3,4,5,6",
            "--initial-train-size", "40",
            "--horizons", "1,2,3,4",
        ],
    },
    {
        "run_id": "E5_v4_clean",
        "module": "src.modeling.runners.run_e5_catboost",
        "args": [
            "--run-id", "E5_v4_clean",
            "--target-mode", "nivel",
            "--feature-mode", "all",
            "--lags", "1,2,3,4,5,6",
            "--initial-train-size", "40",
            "--horizons", "1,2,3,4",
            "--use-inner-tuning",
            "--tuning-metric", "mae",
            "--inner-splits", "3",
            "--iterations-grid", "250,300",
            "--depth-grid", "4,5",
            "--l2-leaf-reg-grid", "3.0,5.0",
        ],
    },
    {
        "run_id": "E7_v3_clean",
        "module": "src.modeling.runners.run_e7_prophet",
        "args": [
            "--run-id", "E7_v3_clean",
            "--target-mode", "nivel",
            "--feature-mode", "corr",
            "--lags", "1,2,3,4,5,6",
            "--initial-train-size", "40",
            "--horizons", "1,2,3,4",
            "--changepoint-prior-scale", "0.2",
        ],
    },
)

FROZEN_E9_SPEC: dict[str, Any] = {
    "run_id": "E9_v2_clean",
    "module": "src.modeling.runners.run_e9_stacking",
    "args": [
        "--run-id", "E9_v2_clean",
        "--meta-model", "huber",
        "--initial-train-size", "12",
        "--horizons", "1,2,3,4",
        "--alpha-grid-size", "40",
        "--inner-splits", "3",
        "--alpha-selection-metric", "mae",
        "--use-only-complete-rows",
        "--reference-run-id", "E1_v5_clean",
        "--extra-reference-run-ids", "E5_v4_clean,E3_v2_clean,E2_v3_clean,E7_v3_clean",
        "--hypothesis-note", "benchmark_operativo_riesgo_controlado",
    ],
}

def _find_latest_run_dir(run_id: str) -> Path:
    candidates = sorted(
        EXPERIMENTS_RUNS_DIR.glob(f"{run_id}_*"),
        key=lambda p: p.name,
        reverse=True,
    )
    for candidate in candidates:
        if candidate.is_dir() and "_aborted" not in candidate.name:
            return candidate
    raise FileNotFoundError(f"No se encontró run_dir para {run_id} en {EXPERIMENTS_RUNS_DIR}")


def _build_e9_curated_table(
    base_run_dirs: dict[str, Path],
    output_path: Path,
) -> None:
    horizons = (1, 2, 3, 4)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for horizon in horizons:
            candidate_run_ids = E9_CANDIDATES_BY_HORIZON[horizon]
            merged_df: pd.DataFrame | None = None
            y_true_columns: list[str] = []
            pred_columns: list[str] = []

            for run_id in candidate_run_ids:
                run_dir = base_run_dirs[run_id]
                pred_path = run_dir / f"predicciones_h{horizon}.csv"
                if not pred_path.exists():
                    raise FileNotFoundError(
                        f"Falta predicciones_h{horizon}.csv en {run_dir} para construir tabla E9"
                    )
                pred_df = pd.read_csv(pred_path)
                date_col = "fecha" if "fecha" in pred_df.columns else "fecha_inicio_semana"
                model_df = pd.DataFrame({
                    "fecha": pd.to_datetime(pred_df[date_col]),
                    f"__y_true_{run_id}": pred_df["y_true"].astype(float),
                    run_id: pred_df["y_pred"].astype(float),
                })
                y_true_columns.append(f"__y_true_{run_id}")
                pred_columns.append(run_id)

                if merged_df is None:
                    merged_df = model_df
                else:
                    merged_df = merged_df.merge(model_df, on="fecha", how="outer", sort=True)

            if merged_df is None or merged_df.empty:
                raise ValueError(f"No se pudo construir tabla E9 para horizonte {horizon}")

            merged_df = merged_df.sort_values("fecha", kind="mergesort").reset_index(drop=True)
            merged_df["y_true"] = merged_df[y_true_columns].bfill(axis=1).iloc[:, 0]
            merged_df = merged_df.drop(columns=y_true_columns)

            ordered_columns = ["fecha", "y_true", *pred_columns]
            merged_df = merged_df[ordered_columns]

            total_models = len(pred_columns)
            merged_df["n_modelos_disponibles"] = merged_df[pred_columns].notna().sum(axis=1)
            merged_df["fila_completa"] = merged_df["n_modelos_disponibles"] == total_models
            merged_df["cobertura_modelos_fila"] = merged_df["n_modelos_disponibles"] / total_models

            sheet_name = f"E9_base_h{horizon}"
            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)


SELECTOR_OOS_WEEKS = 8
SELECTOR_CONFIG = SelectorConfig(rolling_window=4, confidence_k=1.0)


def _run_numeric_selector(
    e1_run_dir: Path,
    e9_run_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    ds = pd.read_excel(DEFAULT_MODEL_DATASET, sheet_name="Sheet1")
    ds["fecha_inicio_semana"] = pd.to_datetime(ds["fecha_inicio_semana"])
    n_weeks = len(ds)
    cutoff_idx = max(0, n_weeks - SELECTOR_OOS_WEEKS - 1)
    cutoff_date = ds["fecha_inicio_semana"].iloc[cutoff_idx]

    results = run_selector_analysis(
        e1_run_dir=e1_run_dir,
        e9_run_dir=e9_run_dir,
        cutoff_date=cutoff_date,
        config=SELECTOR_CONFIG,
    )

    report_text = format_selector_results(results)
    (output_dir / "selector_numerico_adaptativo.txt").write_text(
        report_text + "\n", encoding="utf-8",
    )

    for h, data in results["horizons"].items():
        data["table_oos"].to_csv(
            output_dir / f"selector_oos_h{h}.csv", index=False,
        )

    manifest = {
        "cutoff_date": results["cutoff_date"],
        "cutoff_method": "dynamic",
        "oos_weeks": SELECTOR_OOS_WEEKS,
        "n_weeks_dataset": n_weeks,
        "config": results["config"],
        "metrics_by_horizon": {
            str(h): {"train": data["train"], "oos": data["oos"]}
            for h, data in results["horizons"].items()
        },
    }
    (output_dir / "selector_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    return {
        "cutoff_date": results["cutoff_date"],
        "n_weeks_dataset": n_weeks,
        "oos_weeks": SELECTOR_OOS_WEEKS,
        "output_dir": str(output_dir),
    }


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    outputs: dict[str, Any] = {}
    artifacts: list[str] = []
    metrics: dict[str, Any] = {}

    _py = STAGE_PYTHON["modeling"]

    inputs = {
        "dataset_path": str(DEFAULT_MODEL_DATASET),
        "runs_dir": str(EXPERIMENTS_RUNS_DIR),
        "base_specs": [spec["run_id"] for spec in FROZEN_BASE_SPECS],
        "e9_spec": FROZEN_E9_SPEC["run_id"],
    }

    if not DEFAULT_MODEL_DATASET.exists():
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
            errors=[f"Dataset maestro no encontrado: {DEFAULT_MODEL_DATASET}"],
            notes=[],
            commands=[],
        )

    if context.dry_run:
        for spec in FROZEN_BASE_SPECS:
            command = [_py, "-m", spec["module"], *spec["args"]]
            commands.append(context.run_command("modeling", f"base_{spec['run_id']}", command, check=False))
        commands.append(context.run_command(
            "modeling", "build_e9_table",
            [_py, "-c", "# construir tabla curada E9 temporal"],
            check=False,
        ))
        e9_command = [_py, "-m", FROZEN_E9_SPEC["module"], *FROZEN_E9_SPEC["args"]]
        commands.append(context.run_command("modeling", f"stacking_{FROZEN_E9_SPEC['run_id']}", e9_command, check=False))
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
            notes=["Dry-run: no se ejecutaron runners de modelado."],
            commands=commands,
        )

    # ── Sub-paso 1: ejecutar los 5 runners base ────────────────────────────
    base_run_dirs: dict[str, Path] = {}

    for spec in FROZEN_BASE_SPECS:
        run_id = spec["run_id"]
        command = [_py, "-m", spec["module"], *spec["args"]]
        context.emit(f"Ejecutando runner base {run_id}", stage_name="modeling")
        try:
            cmd_result = context.run_command("modeling", f"base_{run_id}", command)
            commands.append(cmd_result)
            run_dir = _find_latest_run_dir(run_id)
            base_run_dirs[run_id] = run_dir
            outputs[f"base_{run_id}"] = {
                "ok": True,
                "run_dir": str(run_dir),
                "returncode": cmd_result.get("returncode", 0),
            }
            for h in (1, 2, 3, 4):
                pred_path = run_dir / f"predicciones_h{h}.csv"
                if pred_path.exists():
                    artifacts.append(str(pred_path))
        except Exception as exc:
            errors.append(f"Runner base {run_id} falló: {exc}")
            outputs[f"base_{run_id}"] = {"ok": False, "error": str(exc)}
            finished_at = now_text()
            return StageResult(
                stage_name="modeling",
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
                inputs=inputs,
                outputs=outputs,
                artifacts=artifacts,
                metrics=metrics,
                warnings=warnings,
                errors=errors,
                notes=[f"Abortado tras fallo de {run_id}. E9 no se ejecutó."],
                commands=commands,
            )

    # ── Sub-paso 2: construir tabla curada temporal para E9 ─────────────────
    e9_table_dir = ROOT_DIR / "artifacts" / "tmp"
    e9_table_dir.mkdir(parents=True, exist_ok=True)
    e9_table_path = e9_table_dir / f"tabla_e9_curada_{context.run_id}.xlsx"

    context.emit("Construyendo tabla curada temporal para E9", stage_name="modeling")
    try:
        _build_e9_curated_table(base_run_dirs, e9_table_path)
        outputs["e9_curated_table"] = {"ok": True, "path": str(e9_table_path)}
        artifacts.append(str(e9_table_path))
    except Exception as exc:
        errors.append(f"Construcción de tabla E9 falló: {exc}")
        outputs["e9_curated_table"] = {"ok": False, "error": str(exc)}
        finished_at = now_text()
        return StageResult(
            stage_name="modeling",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs=outputs,
            artifacts=artifacts,
            metrics=metrics,
            warnings=warnings,
            errors=errors,
            notes=["Abortado tras fallo al construir tabla E9. Stacking no se ejecutó."],
            commands=commands,
        )

    # ── Sub-paso 3: ejecutar E9 stacking con meta-model huber ───────────────
    e9_command = [
        _py, "-m", FROZEN_E9_SPEC["module"],
        *FROZEN_E9_SPEC["args"],
        "--table-path", str(e9_table_path),
    ]
    context.emit("Ejecutando E9_v2_clean stacking huber", stage_name="modeling")
    try:
        cmd_result = context.run_command("modeling", f"stacking_{FROZEN_E9_SPEC['run_id']}", e9_command)
        commands.append(cmd_result)
        e9_run_dir = _find_latest_run_dir(FROZEN_E9_SPEC["run_id"])
        outputs["stacking_e9"] = {
            "ok": True,
            "run_dir": str(e9_run_dir),
            "returncode": cmd_result.get("returncode", 0),
        }
        for h in (1, 2, 3, 4):
            pred_path = e9_run_dir / f"predicciones_h{h}.csv"
            if pred_path.exists():
                artifacts.append(str(pred_path))
    except Exception as exc:
        errors.append(f"Stacking E9 falló: {exc}")
        outputs["stacking_e9"] = {"ok": False, "error": str(exc)}
        finished_at = now_text()
        return StageResult(
            stage_name="modeling",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs=outputs,
            artifacts=artifacts,
            metrics=metrics,
            warnings=warnings,
            errors=errors,
            notes=["Abortado tras fallo de E9."],
            commands=commands,
        )

    # ── Sub-paso 4: selector numérico adaptativo ─────────────────────────────
    e1_run_dir = base_run_dirs["E1_v5_clean"]
    selector_output_dir = context.artifacts_root / "published" / "selector"

    context.emit("Ejecutando selector numérico adaptativo", stage_name="modeling")
    try:
        selector_result = _run_numeric_selector(e1_run_dir, e9_run_dir, selector_output_dir)
        outputs["numeric_selector"] = {"ok": True, **selector_result}
        for artifact_name in (
            "selector_numerico_adaptativo.txt",
            "selector_manifest.json",
        ):
            artifacts.append(str(selector_output_dir / artifact_name))
        for h in (1, 2, 3, 4):
            csv_path = selector_output_dir / f"selector_oos_h{h}.csv"
            if csv_path.exists():
                artifacts.append(str(csv_path))
    except Exception as exc:
        warnings.append(f"Selector numérico falló (no bloquea pipeline): {exc}")
        outputs["numeric_selector"] = {"ok": False, "error": str(exc)}

    finished_at = now_text()
    return StageResult(
        stage_name="modeling",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
        inputs=inputs,
        outputs=outputs,
        artifacts=artifacts,
        metrics=metrics,
        warnings=warnings,
        errors=[],
        notes=[
            "Runners base E1/E2/E3/E5/E7 ejecutados con args congelados oficiales.",
            "Tabla curada E9 construida con merge por fecha y metadata fila_completa/n_modelos/cobertura.",
            "Stacking E9_v2_clean ejecutado con meta-model huber.",
            "Selector numérico adaptativo ejecutado con cutoff dinámico.",
        ],
        commands=commands,
    )
