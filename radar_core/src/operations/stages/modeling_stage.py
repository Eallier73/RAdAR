from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import DEFAULT_MODEL_DATASET, ROOT_DIR, STAGE_PYTHON
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


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

DIRECTION_POLICY_BY_HORIZON: dict[int, str] = {
    1: "E9_v2_clean",
    2: "E1_v5_clean",
    3: "E9_v2_clean",
    4: "E1_v5_clean",
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


def _build_dual_package(
    e1_run_dir: Path,
    e9_run_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fall_threshold = 0.0

    def direction_label(delta: float) -> str:
        if delta > 0:
            return "sube"
        if delta < 0:
            return "baja"
        return "se_mantiene"

    def load_prediction_frame(run_dir: Path, run_id: str, horizon: int) -> pd.DataFrame:
        path = run_dir / f"predicciones_h{horizon}.csv"
        df = pd.read_csv(path)
        date_col = "fecha" if "fecha" in df.columns else "fecha_inicio_semana"
        normalized = pd.DataFrame({
            "fecha_inicio_semana": df.get("fecha_inicio_semana", df[date_col]),
            "fecha_referencia": df[date_col],
            "horizonte_sem": horizon,
            "y_current": df["y_current"],
            "y_true": df["y_true"],
            "y_pred": df["y_pred"],
            "error": df.get("error"),
            "run_id_origen": run_id,
            "run_dir_origen": str(run_dir),
        })
        normalized["delta_real"] = normalized["y_true"] - normalized["y_current"]
        normalized["delta_predicho"] = normalized["y_pred"] - normalized["y_current"]
        normalized["direction_real"] = normalized["delta_real"].map(direction_label)
        normalized["direction_predicha"] = normalized["delta_predicho"].map(direction_label)
        normalized["direction_correcta"] = (
            normalized["direction_real"] == normalized["direction_predicha"]
        )
        normalized["caida_real"] = normalized["delta_real"] <= fall_threshold
        normalized["alerta_caida_predicha"] = normalized["delta_predicho"] <= fall_threshold
        normalized["deteccion_caida_correcta"] = (
            normalized["caida_real"] == normalized["alerta_caida_predicha"]
        )
        return normalized

    numeric_frames = [load_prediction_frame(e1_run_dir, "E1_v5_clean", h) for h in (1, 2, 3, 4)]
    numeric_df = pd.concat(numeric_frames, ignore_index=True)
    numeric_df["modelo_oficial_numerico"] = "E1_v5_clean"
    numeric_df["prediccion_numerica_oficial"] = numeric_df["y_pred"]
    numeric_df = numeric_df[[
        "fecha_inicio_semana", "fecha_referencia", "horizonte_sem",
        "y_current", "y_true", "prediccion_numerica_oficial",
        "delta_real", "delta_predicho",
        "direction_real", "direction_predicha", "direction_correcta",
        "modelo_oficial_numerico", "run_id_origen", "run_dir_origen",
    ]].sort_values(["horizonte_sem", "fecha_inicio_semana"])

    run_dirs_by_id = {"E1_v5_clean": e1_run_dir, "E9_v2_clean": e9_run_dir}
    direction_pieces: list[pd.DataFrame] = []
    for horizon, run_id in DIRECTION_POLICY_BY_HORIZON.items():
        frame = load_prediction_frame(run_dirs_by_id[run_id], run_id, horizon).copy()
        frame["run_id_direction_oficial"] = run_id
        frame["politica_direccional"] = "9-1-9-1"
        direction_pieces.append(frame[[
            "fecha_inicio_semana", "fecha_referencia", "horizonte_sem",
            "y_current", "y_true", "delta_real", "delta_predicho",
            "direction_real", "direction_predicha", "direction_correcta",
            "run_id_direction_oficial", "politica_direccional", "run_dir_origen",
        ]])
    direction_df = pd.concat(direction_pieces, ignore_index=True).sort_values(
        ["horizonte_sem", "fecha_inicio_semana"]
    )

    fall_frames = [load_prediction_frame(e9_run_dir, "E9_v2_clean", h) for h in (1, 2, 3, 4)]
    fall_df = pd.concat(fall_frames, ignore_index=True)
    fall_df["run_id_alerta_caida_oficial"] = "E9_v2_clean"
    fall_df = fall_df[[
        "fecha_inicio_semana", "fecha_referencia", "horizonte_sem",
        "y_current", "y_true", "delta_real", "delta_predicho",
        "caida_real", "alerta_caida_predicha", "deteccion_caida_correcta",
        "run_id_alerta_caida_oficial", "run_dir_origen",
    ]].sort_values(["horizonte_sem", "fecha_inicio_semana"])

    consolidated = numeric_df.merge(
        direction_df[[
            "fecha_inicio_semana", "horizonte_sem",
            "direction_real", "direction_predicha", "direction_correcta",
            "run_id_direction_oficial", "politica_direccional",
        ]],
        on=["fecha_inicio_semana", "horizonte_sem"],
        how="outer",
        suffixes=("", "_direction"),
    )
    consolidated = consolidated.merge(
        fall_df[[
            "fecha_inicio_semana", "horizonte_sem",
            "caida_real", "alerta_caida_predicha", "deteccion_caida_correcta",
            "run_id_alerta_caida_oficial",
        ]],
        on=["fecha_inicio_semana", "horizonte_sem"],
        how="outer",
        suffixes=("", "_fall"),
    )
    if "direction_real_direction" in consolidated.columns:
        consolidated["direction_real"] = consolidated["direction_real"].fillna(
            consolidated["direction_real_direction"]
        )
        consolidated = consolidated.drop(columns=["direction_real_direction"])
    if "caida_real_fall" in consolidated.columns:
        consolidated["caida_real"] = consolidated["caida_real"].fillna(
            consolidated["caida_real_fall"]
        )
        consolidated = consolidated.drop(columns=["caida_real_fall"])
    consolidated["disponible_prediccion_numerica"] = consolidated["prediccion_numerica_oficial"].notna()
    consolidated["disponible_direction_accuracy"] = consolidated["run_id_direction_oficial"].notna()
    consolidated["disponible_alerta_caida"] = consolidated["run_id_alerta_caida_oficial"].notna()
    consolidated = consolidated.sort_values(["horizonte_sem", "fecha_inicio_semana"])

    numeric_df.to_csv(output_dir / "prediccion_numerica_oficial.csv", index=False)
    direction_df.to_csv(output_dir / "lectura_direccional_oficial.csv", index=False)
    fall_df.to_csv(output_dir / "alertas_caida_oficiales.csv", index=False)
    consolidated.to_csv(output_dir / "salida_dual_operativa_consolidada.csv", index=False)

    return {
        "filas_numerico": len(numeric_df),
        "filas_direction": len(direction_df),
        "filas_caidas": len(fall_df),
        "filas_consolidado": len(consolidated),
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
        "direction_policy": DIRECTION_POLICY_BY_HORIZON,
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
        commands.append(context.run_command(
            "modeling", "empaquetado_dual",
            [_py, "-c", "# empaquetado dual 9-1-9-1"],
            check=False,
        ))
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
                notes=[f"Abortado tras fallo de {run_id}. E9 y el paquete dual no se ejecutaron."],
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
            notes=["Abortado tras fallo al construir tabla E9. Stacking y paquete dual no se ejecutaron."],
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
            notes=["Abortado tras fallo de E9. Paquete dual no se ejecutó."],
            commands=commands,
        )

    # ── Sub-paso 4: empaquetado dual con política 9-1-9-1 ──────────────────
    e1_run_dir = base_run_dirs["E1_v5_clean"]
    dual_output_dir = context.artifacts_root / "published" / "powerbi"

    context.emit("Empaquetando salida dual operativa 9-1-9-1", stage_name="modeling")
    try:
        dual_result = _build_dual_package(e1_run_dir, e9_run_dir, dual_output_dir)
        outputs["dual_package"] = {"ok": True, **dual_result}
        metrics["filas_numerico"] = dual_result["filas_numerico"]
        metrics["filas_direction"] = dual_result["filas_direction"]
        metrics["filas_caidas"] = dual_result["filas_caidas"]
        metrics["filas_consolidado"] = dual_result["filas_consolidado"]
        for csv_name in (
            "prediccion_numerica_oficial.csv",
            "lectura_direccional_oficial.csv",
            "alertas_caida_oficiales.csv",
            "salida_dual_operativa_consolidada.csv",
        ):
            artifacts.append(str(dual_output_dir / csv_name))
    except Exception as exc:
        errors.append(f"Empaquetado dual falló: {exc}")
        outputs["dual_package"] = {"ok": False, "error": str(exc)}
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
            notes=["Abortado tras fallo del empaquetado dual."],
            commands=commands,
        )

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
            "Paquete dual operativo generado con política direccional 9-1-9-1.",
        ],
        commands=commands,
    )
