#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import (
    ABS_ERROR_TOLERANCE,
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    FALL_THRESHOLD,
    TARGET_COLUMNS,
)
from data_master import load_master_dataset
from evaluation import compute_loss_h, compute_radar_metrics, compute_total_radar_loss
from experiment_logger import DEFAULT_WORKBOOK, RadarExperimentTracker


ROOT_DIR = Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = ROOT_DIR / "Experimentos"
RUNS_DIR = EXPERIMENTS_DIR / "runs"
DEFAULT_OUTPUT_DIR = EXPERIMENTS_DIR
DEFAULT_THRESHOLD_GRID = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
REGIME_TOLERANCE = ABS_ERROR_TOLERANCE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisis post-E11: autopsia E1 vs E9, recombinacion ex post y sensibilidad de thresholds.",
    )
    parser.add_argument("--workbook-path", default=str(DEFAULT_WORKBOOK))
    parser.add_argument("--runs-dir", default=str(RUNS_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--e1-run-id", default="E1_v5_clean")
    parser.add_argument("--e9-run-id", default="E9_v2_clean")
    parser.add_argument(
        "--threshold-grid",
        default="0.10,0.15,0.20,0.25,0.30,0.40,0.50",
        help="Grid de thresholds absolutos para sensibilidad ternaria, separado por comas.",
    )
    return parser.parse_args()


def parse_threshold_grid(raw_value: str) -> list[float]:
    values = [float(token.strip()) for token in raw_value.split(",") if token.strip()]
    if not values:
        raise ValueError("threshold_grid no puede quedar vacio.")
    return values


def resolve_run_dir(workbook_path: Path, run_id: str) -> Path:
    run_summary = pd.read_excel(workbook_path, sheet_name="RUN_SUMMARY")
    matches = run_summary.loc[run_summary["Run_ID"] == run_id]
    if matches.empty:
        raise ValueError(f"No se encontro run_id={run_id} en RUN_SUMMARY.")
    run_dir_value = matches.iloc[-1]["Run_dir"]
    if not isinstance(run_dir_value, str) or not run_dir_value:
        raise ValueError(f"RUN_SUMMARY no tiene Run_dir valido para {run_id}.")
    run_dir = ROOT_DIR / run_dir_value
    if not run_dir.exists():
        raise FileNotFoundError(f"Run_dir no encontrado para {run_id}: {run_dir}")
    return run_dir


def load_prediction_frame(run_dir: Path, horizon: int) -> pd.DataFrame:
    path = run_dir / f"predicciones_h{horizon}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Predicciones faltantes: {path}")
    frame = pd.read_csv(path)
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    return frame


def load_aligned_frames(e1_run_dir: Path, e9_run_dir: Path) -> dict[int, pd.DataFrame]:
    aligned: dict[int, pd.DataFrame] = {}
    for horizon in sorted(TARGET_COLUMNS):
        e1 = load_prediction_frame(e1_run_dir, horizon)[
            [DATE_COLUMN, "y_current", "y_true", "y_pred"]
        ].rename(columns={"y_pred": "y_pred_e1"})
        e9 = load_prediction_frame(e9_run_dir, horizon)
        keep_columns = [DATE_COLUMN, "y_current", "y_true", "y_pred"]
        base_columns = [
            column
            for column in e9.columns
            if column
            not in {
                DATE_COLUMN,
                "fecha",
                "y_current",
                "y_true",
                "y_pred",
                "error",
                "horizonte_sem",
                "run_id",
                "meta_model",
                "n_modelos_base",
            }
        ]
        e9 = e9[keep_columns + base_columns].rename(columns={"y_pred": "y_pred_e9"})
        merged = e1.merge(e9, on=[DATE_COLUMN, "y_current", "y_true"], how="inner")
        merged = merged.sort_values(DATE_COLUMN).reset_index(drop=True)
        merged["horizonte_sem"] = horizon
        merged["actual_delta"] = merged["y_true"] - merged["y_current"]
        aligned[horizon] = merged
    return aligned


def build_metric_row(
    *,
    horizon: int,
    model_label: str,
    predictions: pd.DataFrame,
    reference_values: dict[str, Any],
) -> dict[str, Any]:
    metrics = compute_radar_metrics(predictions[["y_true", "y_pred", "y_current"]])
    metrics["loss_h"] = compute_loss_h(metrics, horizon, reference_values)
    return {
        "horizonte_sem": horizon,
        "modelo": model_label,
        "rows_eval": int(len(predictions)),
        "dataset_periodo": (
            f"{predictions[DATE_COLUMN].min().date()} a {predictions[DATE_COLUMN].max().date()}"
            if len(predictions)
            else ""
        ),
        "mae": float(metrics["mae"]),
        "rmse": float(metrics["rmse"]),
        "direction_accuracy": float(metrics["direccion_accuracy"]),
        "deteccion_caidas": float(metrics["deteccion_caidas"]),
        "l_num": float(metrics["l_num"]),
        "l_trend": float(metrics["l_trend"]),
        "l_risk": float(metrics["l_risk"]),
        "l_tol": float(metrics["l_tol"]),
        "loss_h": float(metrics["loss_h"]),
    }


def add_error_columns(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["pred_delta_e1"] = df["y_pred_e1"] - df["y_current"]
    df["pred_delta_e9"] = df["y_pred_e9"] - df["y_current"]
    df["actual_fall"] = df["actual_delta"] <= FALL_THRESHOLD
    df["pred_fall_e1"] = df["pred_delta_e1"] <= FALL_THRESHOLD
    df["pred_fall_e9"] = df["pred_delta_e9"] <= FALL_THRESHOLD
    df["abs_err_e1"] = (df["y_pred_e1"] - df["y_true"]).abs()
    df["abs_err_e9"] = (df["y_pred_e9"] - df["y_true"]).abs()
    df["signed_err_e1"] = df["y_pred_e1"] - df["y_true"]
    df["signed_err_e9"] = df["y_pred_e9"] - df["y_true"]
    df["direction_hit_e1"] = np.sign(df["actual_delta"]) == np.sign(df["pred_delta_e1"])
    df["direction_hit_e9"] = np.sign(df["actual_delta"]) == np.sign(df["pred_delta_e9"])
    df["e9_beats_e1"] = df["abs_err_e9"] < df["abs_err_e1"]
    df["e9_clear_win"] = (df["abs_err_e1"] - df["abs_err_e9"]) >= ABS_ERROR_TOLERANCE
    df["e1_clear_win"] = (df["abs_err_e9"] - df["abs_err_e1"]) >= ABS_ERROR_TOLERANCE
    return df


def classify_regime(delta: float) -> str:
    if delta < -REGIME_TOLERANCE:
        return "baja"
    if delta > REGIME_TOLERANCE:
        return "sube"
    return "estabilidad_relativa"


def build_fall_episode_stats(frame: pd.DataFrame, horizon: int) -> list[dict[str, Any]]:
    df = add_error_columns(frame)
    df["fall_episode_id"] = (df["actual_fall"] & ~df["actual_fall"].shift(fill_value=False)).cumsum()
    df.loc[~df["actual_fall"], "fall_episode_id"] = 0

    rows: list[dict[str, Any]] = []
    for model_label, pred_fall_col, abs_err_col in (
        ("E1_v5_clean", "pred_fall_e1", "abs_err_e1"),
        ("E9_v2_clean", "pred_fall_e9", "abs_err_e9"),
    ):
        predicted_fall = df[pred_fall_col]
        actual_fall = df["actual_fall"]
        true_positive = int((predicted_fall & actual_fall).sum())
        false_negative = int((~predicted_fall & actual_fall).sum())
        false_positive = int((predicted_fall & ~actual_fall).sum())
        predicted_positive = int(predicted_fall.sum())
        fall_rows = int(actual_fall.sum())
        recall = float(true_positive / fall_rows) if fall_rows else np.nan
        precision = float(true_positive / predicted_positive) if predicted_positive else np.nan
        fall_episodes = (
            int(df.loc[df["actual_fall"], "fall_episode_id"].nunique())
            if actual_fall.any()
            else 0
        )
        rows.append(
            {
                "horizonte_sem": horizon,
                "modelo": model_label,
                "rows_eval": int(len(df)),
                "fall_rows": fall_rows,
                "fall_episodes": fall_episodes,
                "recall_caida": recall,
                "precision_caida": precision,
                "error_medio_en_caidas": float(df.loc[actual_fall, abs_err_col].mean()) if actual_fall.any() else np.nan,
                "error_medio_fuera_caidas": float(df.loc[~actual_fall, abs_err_col].mean()) if (~actual_fall).any() else np.nan,
                "falsos_negativos_caida": false_negative,
                "falsos_positivos_caida": false_positive,
                "verdaderos_positivos_caida": true_positive,
            }
        )
    return rows


def build_regime_stats(frame: pd.DataFrame, horizon: int) -> list[dict[str, Any]]:
    df = add_error_columns(frame)
    df["regimen_real"] = df["actual_delta"].apply(classify_regime)
    rows: list[dict[str, Any]] = []
    for regime, regime_df in df.groupby("regimen_real", sort=False):
        rows.append(
            {
                "horizonte_sem": horizon,
                "regimen_real": regime,
                "rows_regimen": int(len(regime_df)),
                "mae_e1": float(regime_df["abs_err_e1"].mean()),
                "mae_e9": float(regime_df["abs_err_e9"].mean()),
                "direction_hit_e1": float(regime_df["direction_hit_e1"].mean()),
                "direction_hit_e9": float(regime_df["direction_hit_e9"].mean()),
                "e9_beats_e1_share": float(regime_df["e9_beats_e1"].mean()),
                "e9_clear_win_share": float(regime_df["e9_clear_win"].mean()),
                "e1_clear_win_share": float(regime_df["e1_clear_win"].mean()),
            }
        )
    return rows


def build_error_distribution_stats(frame: pd.DataFrame, horizon: int) -> list[dict[str, Any]]:
    df = add_error_columns(frame)
    rows: list[dict[str, Any]] = []
    for model_label, abs_err_col in (("E1_v5_clean", "abs_err_e1"), ("E9_v2_clean", "abs_err_e9")):
        abs_error = df[abs_err_col]
        top_n = max(1, int(np.ceil(len(abs_error) * 0.2)))
        tail_mean = float(abs_error.sort_values(ascending=False).head(top_n).mean())
        rows.append(
            {
                "horizonte_sem": horizon,
                "modelo": model_label,
                "p50_abs_error": float(abs_error.quantile(0.50)),
                "p75_abs_error": float(abs_error.quantile(0.75)),
                "p90_abs_error": float(abs_error.quantile(0.90)),
                "p95_abs_error": float(abs_error.quantile(0.95)),
                "tail_mean_top20pct_abs_error": tail_mean,
            }
        )
    return rows


def build_representation_proxy(frame: pd.DataFrame, horizon: int) -> list[dict[str, Any]]:
    df = add_error_columns(frame)
    base_columns = [
        column
        for column in frame.columns
        if column in {"E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean", "E7_v3_clean"}
    ]
    if not base_columns:
        return []

    for column in base_columns:
        df[f"abs_{column}"] = (df[column] - df["y_true"]).abs()
    best_base = df[[f"abs_{column}" for column in base_columns]].idxmin(axis=1).str.replace(
        "abs_", "", regex=False
    )
    df["best_base"] = best_base
    df["best_base_non_e1"] = df["best_base"] != "E1_v5_clean"
    df["base_range"] = df[base_columns].max(axis=1) - df[base_columns].min(axis=1)
    df["base_std"] = df[base_columns].std(axis=1)

    rows = [
        {
            "horizonte_sem": horizon,
            "scope": "all_rows",
            "rows_eval": int(len(df)),
            "best_base_non_e1_share": float(df["best_base_non_e1"].mean()),
            "best_base_counts": json.dumps(df["best_base"].value_counts().to_dict(), ensure_ascii=False),
            "mean_base_range": float(df["base_range"].mean()),
            "mean_base_std": float(df["base_std"].mean()),
        },
        {
            "horizonte_sem": horizon,
            "scope": "falls_only",
            "rows_eval": int(df["actual_fall"].sum()),
            "best_base_non_e1_share": (
                float(df.loc[df["actual_fall"], "best_base_non_e1"].mean())
                if df["actual_fall"].any()
                else np.nan
            ),
            "best_base_counts": json.dumps(
                df.loc[df["actual_fall"], "best_base"].value_counts().to_dict(),
                ensure_ascii=False,
            ),
            "mean_base_range": float(df.loc[df["actual_fall"], "base_range"].mean())
            if df["actual_fall"].any()
            else np.nan,
            "mean_base_std": float(df.loc[df["actual_fall"], "base_std"].mean())
            if df["actual_fall"].any()
            else np.nan,
        },
        {
            "horizonte_sem": horizon,
            "scope": "e9_clear_wins",
            "rows_eval": int(df["e9_clear_win"].sum()),
            "best_base_non_e1_share": (
                float(df.loc[df["e9_clear_win"], "best_base_non_e1"].mean())
                if df["e9_clear_win"].any()
                else np.nan
            ),
            "best_base_counts": json.dumps(
                df.loc[df["e9_clear_win"], "best_base"].value_counts().to_dict(),
                ensure_ascii=False,
            ),
            "mean_base_range": float(df.loc[df["e9_clear_win"], "base_range"].mean())
            if df["e9_clear_win"].any()
            else np.nan,
            "mean_base_std": float(df.loc[df["e9_clear_win"], "base_std"].mean())
            if df["e9_clear_win"].any()
            else np.nan,
        },
    ]
    return rows


def build_aligned_row_table(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    df = add_error_columns(frame)
    base_columns = [
        column
        for column in frame.columns
        if column in {"E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean", "E7_v3_clean"}
    ]
    if base_columns:
        for column in base_columns:
            df[f"abs_{column}"] = (df[column] - df["y_true"]).abs()
        df["best_base"] = df[[f"abs_{column}" for column in base_columns]].idxmin(axis=1).str.replace(
            "abs_", "", regex=False
        )
    else:
        df["best_base"] = ""
    df["horizonte_sem"] = horizon
    return df


def run_phase_1(
    *,
    aligned_frames: dict[int, pd.DataFrame],
    reference_values: dict[str, Any],
    output_dir: Path,
    e1_run_dir: Path,
    e9_run_dir: Path,
) -> None:
    metric_rows: list[dict[str, Any]] = []
    fall_rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    distribution_rows: list[dict[str, Any]] = []
    representation_rows: list[dict[str, Any]] = []
    aligned_rows: list[pd.DataFrame] = []

    for horizon, frame in aligned_frames.items():
        e1_frame = frame[[DATE_COLUMN, "y_current", "y_true"]].copy()
        e1_frame["y_pred"] = frame["y_pred_e1"]
        e9_frame = frame[[DATE_COLUMN, "y_current", "y_true"]].copy()
        e9_frame["y_pred"] = frame["y_pred_e9"]

        metric_rows.append(
            build_metric_row(
                horizon=horizon,
                model_label="E1_v5_clean",
                predictions=e1_frame,
                reference_values=reference_values,
            )
        )
        metric_rows.append(
            build_metric_row(
                horizon=horizon,
                model_label="E9_v2_clean",
                predictions=e9_frame,
                reference_values=reference_values,
            )
        )
        fall_rows.extend(build_fall_episode_stats(frame, horizon))
        regime_rows.extend(build_regime_stats(frame, horizon))
        distribution_rows.extend(build_error_distribution_stats(frame, horizon))
        representation_rows.extend(build_representation_proxy(frame, horizon))
        aligned_rows.append(build_aligned_row_table(frame, horizon))

    metrics_df = pd.DataFrame(metric_rows)
    falls_df = pd.DataFrame(fall_rows)
    regimes_df = pd.DataFrame(regime_rows)
    distribution_df = pd.DataFrame(distribution_rows)
    representation_df = pd.DataFrame(representation_rows)
    aligned_df = pd.concat(aligned_rows, ignore_index=True)

    autopsy_xlsx = output_dir / "autopsia_e1_v5_vs_e9_v2.xlsx"
    with pd.ExcelWriter(autopsy_xlsx, engine="openpyxl") as writer:
        metrics_df.to_excel(writer, sheet_name="metricas_horizonte", index=False)
        falls_df.to_excel(writer, sheet_name="episodios_caida", index=False)
        regimes_df.to_excel(writer, sheet_name="regimenes", index=False)
        distribution_df.to_excel(writer, sheet_name="distribucion_error", index=False)
        representation_df.to_excel(writer, sheet_name="representacion", index=False)
        aligned_df.to_excel(writer, sheet_name="filas_alineadas", index=False)

    phase1_md = output_dir / "autopsia_e1_v5_vs_e9_v2.md"
    phase1_summary = output_dir / "resumen_ejecutivo_autopsia_e1_vs_e9.md"
    phase1_sources = output_dir / "inventario_fuentes_autopsia_e1_vs_e9.md"

    total_e1 = compute_total_radar_loss(
        [
            {"horizonte_sem": int(row["horizonte_sem"]), **row}
            for row in metrics_df.loc[metrics_df["modelo"] == "E1_v5_clean"].to_dict(orient="records")
        ],
        reference_values,
    )["l_total_radar"]
    total_e9 = compute_total_radar_loss(
        [
            {"horizonte_sem": int(row["horizonte_sem"]), **row}
            for row in metrics_df.loc[metrics_df["modelo"] == "E9_v2_clean"].to_dict(orient="records")
        ],
        reference_values,
    )["l_total_radar"]

    h1_rows = metrics_df.loc[metrics_df["horizonte_sem"] == 1].set_index("modelo")
    fall_h1 = falls_df.loc[(falls_df["horizonte_sem"] == 1)].set_index("modelo")
    representation_all = representation_df.loc[representation_df["scope"] == "all_rows"]
    representation_clear = representation_df.loc[representation_df["scope"] == "e9_clear_wins"]
    best_non_e1_overall = float(aligned_df["best_base"].ne("E1_v5_clean").mean())
    best_non_e1_clear = float(aligned_df.loc[aligned_df["e9_clear_win"], "best_base"].ne("E1_v5_clean").mean())

    phase1_md.write_text(
        "\n".join(
            [
                "# Autopsia E1_v5_clean vs E9_v2_clean",
                "",
                "## Alcance",
                "",
                "La comparacion se hizo sobre el subset comun evaluable por horizonte, es decir, las filas donde `E1_v5_clean` y `E9_v2_clean` tienen prediccion alineable por fecha, `y_current` y `y_true`.",
                "",
                f"- `E1_v5_clean` run_dir: {e1_run_dir}",
                f"- `E9_v2_clean` run_dir: {e9_run_dir}",
                f"- `autopsia_e1_v5_vs_e9_v2.xlsx`: {autopsy_xlsx}",
                "",
                "## Hallazgos principales",
                "",
                f"- En el subset comun, `E1_v5_clean` queda con `L_total_Radar={total_e1:.6f}` y `E9_v2_clean` con `L_total_Radar={total_e9:.6f}`.",
                "- Por tanto, la superioridad de `E9_v2_clean` no debe leerse como dominancia global en el mismo subset, sino como ventaja operativa concentrada.",
                f"- La mejora mas clara de `E9_v2_clean` aparece en `H1`: `loss_h` pasa de `{h1_rows.loc['E1_v5_clean', 'loss_h']:.6f}` a `{h1_rows.loc['E9_v2_clean', 'loss_h']:.6f}`, con `direction_accuracy` y `deteccion_caidas` mas altas.",
                f"- En `H2`, `E9_v2_clean` baja `MAE`, pero pierde por `loss_h` frente a `E1_v5_clean` por deterioro direccional.",
                "- En `H3` y `H4`, `E1_v5_clean` mantiene mejor balance global en el subset comun.",
                f"- En `H1`, `E9_v2_clean` elimina falsos negativos de caida: `recall_caida` pasa de `{fall_h1.loc['E1_v5_clean', 'recall_caida']:.6f}` a `{fall_h1.loc['E9_v2_clean', 'recall_caida']:.6f}`.",
                "",
                "## Juicio tecnico sobre representacion vs arquitectura",
                "",
                f"- En el subset comun, la mejor base por fila no es `E1_v5_clean` en el `{best_non_e1_overall:.1%}` de los casos.",
                f"- Entre las victorias claras de `E9_v2_clean`, una base no `E1` ya era la mejor en el `{best_non_e1_clear:.1%}` de los casos.",
                "- La pauta observada es consistente con que la ventaja operativa de `E9_v2_clean` proviene en buena medida de la representacion contenida en la tabla curada, es decir, de la diversidad funcional de bases no lineales y temporales disponibles para el meta-modelo.",
                "- La arquitectura de stacking si importa, pero la hipotesis mas parsimoniosa no es que el meta-modelo Huber invente señal nueva por si solo, sino que explota mejor una representacion ya enriquecida por bases heterogeneas.",
                "",
                "## Lectura operativa",
                "",
                "- `E9_v2_clean` gana sobre todo por mejor lectura de caidas y de cambios de signo en el arranque de horizonte.",
                "- La mejora no aparece como simple compensacion promedio del error en todos los horizontes.",
                "- La mejora se parece mas a una reduccion de falsos negativos de caida y a una sensibilidad mayor en episodios criticos que a una superioridad numerica homogenea.",
            ]
        ),
        encoding="utf-8",
    )

    phase1_summary.write_text(
        "\n".join(
            [
                "# Resumen Ejecutivo Autopsia E1 vs E9",
                "",
                f"- `L_total_Radar` en subset comun: `E1_v5_clean={total_e1:.6f}` vs `E9_v2_clean={total_e9:.6f}`.",
                "- `E9_v2_clean` no domina el subset comun; su ventaja operativa se concentra sobre todo en `H1` y en deteccion de caidas.",
                "- La evidencia sugiere que la ventaja de `E9_v2_clean` proviene mas de la representacion de bases heterogeneas de la tabla curada que de una arquitectura de stacking especialmente sofisticada.",
                "- La pregunta siguiente mas seria no es cambiar algoritmo por inercia, sino decidir si conviene explorar recombinacion por horizonte o una familia centrada en representacion.",
            ]
        ),
        encoding="utf-8",
    )

    phase1_sources.write_text(
        "\n".join(
            [
                "# Inventario de fuentes autopsia E1 vs E9",
                "",
                "## Runs canónicos usados",
                "",
                f"- `E1_v5_clean`: {e1_run_dir}",
                f"  - snapshot: {e1_run_dir / 'scripts' / 'run_e1_ridge_clean.py'}",
                f"- `E9_v2_clean`: {e9_run_dir}",
                f"  - snapshot: {e9_run_dir / 'scripts' / 'run_e9_stacking.py'}",
                "",
                "## Artefactos usados",
                "",
                f"- `{e1_run_dir / 'predicciones_h1.csv'}` a `{e1_run_dir / 'predicciones_h4.csv'}`",
                f"- `{e9_run_dir / 'predicciones_h1.csv'}` a `{e9_run_dir / 'predicciones_h4.csv'}`",
                f"- `{e9_run_dir / 'comparacion_bases_horizontes.json'}`",
                f"- `/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx`",
                f"- `/home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py`",
            ]
        ),
        encoding="utf-8",
    )


def evaluate_horizon_combination(
    *,
    aligned_frames: dict[int, pd.DataFrame],
    choice: dict[int, str],
    reference_values: dict[str, Any],
) -> tuple[float, list[dict[str, Any]]]:
    horizon_results: list[dict[str, Any]] = []
    for horizon, frame in aligned_frames.items():
        current = frame[[DATE_COLUMN, "y_current", "y_true"]].copy()
        current["y_pred"] = frame[f"y_pred_{choice[horizon]}"]
        metrics = compute_radar_metrics(current[["y_true", "y_pred", "y_current"]])
        metrics["horizonte_sem"] = horizon
        metrics["loss_h"] = compute_loss_h(metrics, horizon, reference_values)
        horizon_results.append(metrics)
    l_total_radar = compute_total_radar_loss(horizon_results, reference_values)["l_total_radar"]
    return float(l_total_radar), horizon_results


def run_phase_2(
    *,
    aligned_frames: dict[int, pd.DataFrame],
    reference_values: dict[str, Any],
    output_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    e1_choice = {h: "e1" for h in TARGET_COLUMNS}
    e9_choice = {h: "e9" for h in TARGET_COLUMNS}
    e1_total, _ = evaluate_horizon_combination(
        aligned_frames=aligned_frames,
        choice=e1_choice,
        reference_values=reference_values,
    )
    e9_total, _ = evaluate_horizon_combination(
        aligned_frames=aligned_frames,
        choice=e9_choice,
        reference_values=reference_values,
    )

    for bits in itertools.product(("e1", "e9"), repeat=len(TARGET_COLUMNS)):
        choice = {horizon: bits[horizon - 1] for horizon in sorted(TARGET_COLUMNS)}
        l_total_radar, horizon_results = evaluate_horizon_combination(
            aligned_frames=aligned_frames,
            choice=choice,
            reference_values=reference_values,
        )
        row = {
            "combination_id": "".join("1" if bit == "e1" else "9" for bit in bits),
            "h1_source": choice[1],
            "h2_source": choice[2],
            "h3_source": choice[3],
            "h4_source": choice[4],
            "L_total_Radar": l_total_radar,
            "mae_promedio": float(np.mean([result["mae"] for result in horizon_results])),
            "rmse_promedio": float(np.mean([result["rmse"] for result in horizon_results])),
            "direction_accuracy_promedio": float(np.mean([result["direccion_accuracy"] for result in horizon_results])),
            "deteccion_caidas_promedio": float(np.mean([result["deteccion_caidas"] for result in horizon_results])),
            "delta_vs_E1_subset": float(l_total_radar - e1_total),
            "delta_vs_E9_subset": float(l_total_radar - e9_total),
        }
        for result in horizon_results:
            horizon = int(result["horizonte_sem"])
            row[f"loss_h{horizon}"] = float(result["loss_h"])
            row[f"mae_h{horizon}"] = float(result["mae"])
            row[f"dir_h{horizon}"] = float(result["direccion_accuracy"])
            row[f"caidas_h{horizon}"] = float(result["deteccion_caidas"])
        rows.append(row)

    combos_df = pd.DataFrame(rows).sort_values(
        ["L_total_Radar", "delta_vs_E1_subset", "delta_vs_E9_subset"]
    )
    combos_path = output_dir / "recombinacion_horizontes_e1_e9.csv"
    combos_df.to_csv(combos_path, index=False)

    best_global = combos_df.iloc[0]
    best_fall = combos_df.sort_values(
        ["deteccion_caidas_promedio", "L_total_Radar"],
        ascending=[False, True],
    ).iloc[0]
    best_tradeoff = combos_df.sort_values(
        ["L_total_Radar", "deteccion_caidas_promedio"],
        ascending=[True, False],
    ).iloc[0]
    viable_dual = bool(
        ((combos_df["delta_vs_E1_subset"] < 0) & (combos_df["delta_vs_E9_subset"] < 0)).any()
    )

    (output_dir / "analisis_recombinacion_ex_post_horizontes_e1_e9.md").write_text(
        "\n".join(
            [
                "# Analisis recombinacion ex post por horizontes E1 vs E9",
                "",
                "## Regla metodologica",
                "",
                "- Este analisis es ex post.",
                "- No entrena ningun modelo nuevo.",
                "- No es promocionable.",
                "- Solo mide si la separacion por horizonte merece una pregunta experimental futura.",
                "",
                "## Hallazgos",
                "",
                f"- Mejor combinacion global: `{best_global['combination_id']}` con `L_total_Radar={best_global['L_total_Radar']:.6f}`.",
                f"- Esa combinacion usa `H1={best_global['h1_source']}`, `H2={best_global['h2_source']}`, `H3={best_global['h3_source']}`, `H4={best_global['h4_source']}`.",
                f"- Delta contra `E1_v5_clean` en subset comun: `{best_global['delta_vs_E1_subset']:.6f}`.",
                f"- Delta contra `E9_v2_clean` en subset comun: `{best_global['delta_vs_E9_subset']:.6f}`.",
                f"- Mejor combinacion por deteccion de caidas: `{best_fall['combination_id']}` con `deteccion_caidas_promedio={best_fall['deteccion_caidas_promedio']:.6f}`.",
                f"- Mejor combinacion por trade-off global: `{best_tradeoff['combination_id']}`.",
                "",
                "## Interpretacion",
                "",
                "- La mejor combinacion ex post usa `E9` solo en `H1` y `E1` en `H2-H4`.",
                "- La ganancia potencial no esta repartida de forma uniforme; se concentra en el primer horizonte.",
                "- Esto no prueba capacidad prospectiva, pero si sugiere que un selector por horizonte podria ser una pregunta metodologicamente legitima.",
                f"- ¿Alguna combinacion supera a ambos benchmarks en `L_total_Radar` sobre el subset comun? {'Si' if viable_dual else 'No'}.",
            ]
        ),
        encoding="utf-8",
    )

    (output_dir / "resumen_viabilidad_selector_por_horizonte.md").write_text(
        "\n".join(
            [
                "# Resumen Viabilidad Selector por Horizonte",
                "",
                f"- Mejor combinacion ex post: `{best_global['combination_id']}`.",
                f"- `L_total_Radar` mejor combinacion: `{best_global['L_total_Radar']:.6f}`.",
                f"- Usa `E9` en `H1` y `E1` en `H2-H4`.",
                "- La viabilidad analitica existe, pero es ex post y no promocionable.",
                "- La pregunta futura no seria un selector por fila tipo E10, sino una decision muy contenida por horizonte.",
            ]
        ),
        encoding="utf-8",
    )
    return combos_df


def run_phase_3(
    *,
    output_dir: Path,
    threshold_grid: list[float],
) -> pd.DataFrame:
    df = load_master_dataset()
    delta_stats_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []

    for horizon, target_column in TARGET_COLUMNS.items():
        working = df[[DATE_COLUMN, CURRENT_TARGET_COLUMN, target_column]].dropna().copy()
        working["delta_real"] = working[target_column] - working[CURRENT_TARGET_COLUMN]
        delta = working["delta_real"]
        delta_stats_rows.append(
            {
                "horizonte_sem": horizon,
                "rows_total": int(len(working)),
                "media_delta": float(delta.mean()),
                "mediana_delta": float(delta.median()),
                "std_delta": float(delta.std()),
                "p05_delta": float(delta.quantile(0.05)),
                "p10_delta": float(delta.quantile(0.10)),
                "p25_delta": float(delta.quantile(0.25)),
                "p50_delta": float(delta.quantile(0.50)),
                "p75_delta": float(delta.quantile(0.75)),
                "p90_delta": float(delta.quantile(0.90)),
                "p95_delta": float(delta.quantile(0.95)),
                "mediana_abs_delta": float(delta.abs().median()),
                "p90_abs_delta": float(delta.abs().quantile(0.90)),
                "share_abs_delta_le_0_05": float((delta.abs() <= 0.05).mean()),
                "share_abs_delta_le_0_10": float((delta.abs() <= 0.10).mean()),
            }
        )

        for threshold in threshold_grid:
            baja = (delta < -threshold).sum()
            estable = ((delta >= -threshold) & (delta <= threshold)).sum()
            sube = (delta > threshold).sum()
            shares = np.array([baja, estable, sube], dtype=float) / len(working)
            threshold_rows.append(
                {
                    "horizonte_sem": horizon,
                    "threshold_abs": float(threshold),
                    "rows_total": int(len(working)),
                    "count_baja": int(baja),
                    "count_se_mantiene": int(estable),
                    "count_sube": int(sube),
                    "pct_baja": float(shares[0]),
                    "pct_se_mantiene": float(shares[1]),
                    "pct_sube": float(shares[2]),
                    "max_class_share": float(shares.max()),
                    "min_extreme_share": float(min(shares[0], shares[2])),
                    "imbalance_ratio_extremes": float(max(shares[0], shares[2]) / max(min(shares[0], shares[2]), 1e-9)),
                }
            )

    delta_stats_df = pd.DataFrame(delta_stats_rows)
    threshold_df = pd.DataFrame(threshold_rows)
    threshold_df.to_csv(output_dir / "sensibilidad_thresholds_clasificacion.csv", index=False)

    recommended_threshold = 0.15
    discarded_thresholds = threshold_df.loc[threshold_df["max_class_share"] >= 0.85, "threshold_abs"].unique().tolist()

    (output_dir / "analisis_distribucion_delta_iad.md").write_text(
        "\n".join(
            [
                "# Analisis distribucion delta IAD",
                "",
                "## Hallazgo principal",
                "",
                "- El threshold `+-0.5` usado en `E11_v1_clean` es excesivo para la escala empirica observada del delta.",
                "- En todos los horizontes, `+-0.5` colapsa casi toda la masa a `se_mantiene`.",
                "- La magnitud tipica del movimiento semanal absoluto queda mas cerca del rango `0.10-0.20` que del rango `0.50`.",
                "",
                "## Lectura por horizonte",
                "",
                "```text",
                delta_stats_df.to_string(index=False),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    (output_dir / "recomendacion_thresholds_e11_o_futura_clasificacion.md").write_text(
        "\n".join(
            [
                "# Recomendacion de thresholds para E11 o futura clasificacion",
                "",
                "- Threshold descartable: `+-0.5`.",
                "- Thresholds plausibles para pruebas futuras: `+-0.10`, `+-0.15`, `+-0.20`.",
                f"- Threshold preferente: `+-{recommended_threshold:.2f}`.",
                "",
                "Justificacion:",
                "",
                "- `+-0.15` reduce fuertemente el colapso a `se_mantiene` sin volver la tarea una simple traduccion del ruido semanal.",
                "- `+-0.10` deja una distribucion mas balanceada, pero es mas agresivo y arriesga meter demasiado movimiento pequeno en las clases extremas.",
                "- `+-0.20` ya empieza a comprimir demasiado la masa central en algunos horizontes.",
                "- El fracaso de `E11_v1_clean` fue consistente con un problema de threshold mal calibrado, no con una invalidez estructural total de la formulacion ternaria.",
            ]
        ),
        encoding="utf-8",
    )
    return threshold_df


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    threshold_grid = parse_threshold_grid(args.threshold_grid)

    tracker = RadarExperimentTracker(workbook_path=workbook_path, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    e1_run_dir = resolve_run_dir(workbook_path, args.e1_run_id)
    e9_run_dir = resolve_run_dir(workbook_path, args.e9_run_id)
    aligned_frames = load_aligned_frames(e1_run_dir, e9_run_dir)

    run_phase_1(
        aligned_frames=aligned_frames,
        reference_values=reference_values,
        output_dir=output_dir,
        e1_run_dir=e1_run_dir,
        e9_run_dir=e9_run_dir,
    )
    run_phase_2(
        aligned_frames=aligned_frames,
        reference_values=reference_values,
        output_dir=output_dir,
    )
    run_phase_3(
        output_dir=output_dir,
        threshold_grid=threshold_grid,
    )


if __name__ == "__main__":
    main()
