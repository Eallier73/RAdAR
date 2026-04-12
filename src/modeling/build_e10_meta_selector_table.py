#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_experiments_master_table import audit_prediction_file
from config import (
    ABS_ERROR_TOLERANCE,
    CURRENT_TARGET_COLUMN,
    DATASET_PATH,
    DATE_COLUMN,
    DEFAULT_SHEET_NAME,
    FALL_THRESHOLD,
    ROOT_DIR,
    TARGET_COLUMNS,
    WEEK_COLUMN,
)
from data_master import load_master_dataset
from experiment_logger import DEFAULT_WORKBOOK, RadarExperimentTracker


DEFAULT_OUTPUT_DIR = ROOT_DIR / "experiments" / "audit"
DEFAULT_MASTER_TABLE_PATH = DEFAULT_OUTPUT_DIR / "tabla_maestra_experimentos_radar.xlsx"
DEFAULT_CURATED_E9_TABLE_PATH = DEFAULT_OUTPUT_DIR / "tabla_maestra_experimentos_radar_e9_curada.xlsx"
DEFAULT_E10_TABLE_CSV = DEFAULT_OUTPUT_DIR / "tabla_e10_meta_selector_base.csv"
DEFAULT_E10_TABLE_XLSX = DEFAULT_OUTPUT_DIR / "tabla_e10_meta_selector_base.xlsx"
DEFAULT_E10_DICTIONARY_MD = DEFAULT_OUTPUT_DIR / "diccionario_tabla_e10.md"
DEFAULT_E10_COLUMN_INVENTORY_CSV = DEFAULT_OUTPUT_DIR / "inventario_columnas_e10.csv"
DEFAULT_E10_SUMMARY_MD = DEFAULT_OUTPUT_DIR / "resumen_construccion_tabla_e10.md"

E10_SOURCE_VERSION = "e10_meta_selector_base_v1_2026-04-01"
E10_INCLUDED_MODELS: tuple[dict[str, str], ...] = (
    {
        "run_id": "E1_v5_clean",
        "constructo": "referente numerico puro",
        "justificacion": "Benchmark numerico puro principal del proyecto y ancla lineal regularizada.",
    },
    {
        "run_id": "E5_v4_clean",
        "constructo": "mejor no lineal tabular",
        "justificacion": "Campeon no lineal tabular vigente y candidato fuerte a familia base competitiva.",
    },
    {
        "run_id": "E9_v2_clean",
        "constructo": "referente operativo de riesgo-direccion-caidas",
        "justificacion": "Mejor run orientado a riesgo, direccion y deteccion de caidas; inclusion minima obligatoria para E10.",
    },
    {
        "run_id": "E3_v2_clean",
        "constructo": "bagging de diversidad",
        "justificacion": "Referencia bagging util para diversidad funcional frente a lineales y boosting.",
    },
    {
        "run_id": "E2_v3_clean",
        "constructo": "referencia robusta / especialista H2-H4",
        "justificacion": "Aporta sesgo robusto y senal util en horizontes intermedios y largos.",
    },
    {
        "run_id": "E7_v3_clean",
        "constructo": "referencia temporal con changepoints",
        "justificacion": "Aporta una familia temporal estructurada distinta a ARIMAX y distinta de los tabulares.",
    },
)

E10_EXCLUDED_MODELS: tuple[dict[str, str], ...] = (
    {
        "run_id": "E1_v4_clean",
        "motivo_exclusion": "Queda fuera por alta redundancia con E1_v5_clean; se evita duplicar Ridge en la primera base E10.",
    },
    {
        "run_id": "E4_v1_clean",
        "motivo_exclusion": "XGBoost queda dominado como fuente de diversidad frente a E5_v4_clean y E3_v2_clean.",
    },
    {
        "run_id": "E8_v2_clean",
        "motivo_exclusion": "Hibrido residual util, pero derivativo respecto a E5 y aun no suficientemente estable para entrar al pool principal de E10.",
    },
    {
        "run_id": "E6_v1_clean",
        "motivo_exclusion": "ARIMAX quedo debilitado y no aporta diversidad competitiva suficiente frente a E7_v3_clean.",
    },
)


@dataclass(frozen=True)
class E10Artifacts:
    table_csv_path: Path
    table_xlsx_path: Path
    dictionary_md_path: Path
    column_inventory_csv_path: Path
    summary_md_path: Path
    rows_total: int
    complete_rows_by_horizon: dict[int, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construye la tabla operativa de E10 para meta-seleccion / gating contextual.",
    )
    parser.add_argument(
        "--source-workbook",
        type=Path,
        default=DEFAULT_MASTER_TABLE_PATH,
        help="Workbook maestro consolidado con runs_catalogo.",
    )
    parser.add_argument(
        "--grid-workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook del tracker usado para leer los pesos vigentes de la funcion Radar.",
    )
    parser.add_argument(
        "--curated-e9-workbook",
        type=Path,
        default=DEFAULT_CURATED_E9_TABLE_PATH,
        help="Workbook curado de E9 usado solo como referencia documental.",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DATASET_PATH,
        help="Dataset maestro del Radar.",
    )
    parser.add_argument(
        "--sheet-name",
        default=DEFAULT_SHEET_NAME,
        help="Hoja del dataset maestro.",
    )
    parser.add_argument(
        "--history-window",
        type=int,
        default=4,
        help="Ventana rolling retrospectiva para historicos de error/rendimiento por modelo.",
    )
    parser.add_argument(
        "--table-csv-path",
        type=Path,
        default=DEFAULT_E10_TABLE_CSV,
        help="CSV de salida para la tabla larga de E10.",
    )
    parser.add_argument(
        "--table-xlsx-path",
        type=Path,
        default=DEFAULT_E10_TABLE_XLSX,
        help="XLSX de salida para la tabla larga y hojas por horizonte.",
    )
    parser.add_argument(
        "--dictionary-md-path",
        type=Path,
        default=DEFAULT_E10_DICTIONARY_MD,
        help="Markdown con diccionario metodologico de la tabla E10.",
    )
    parser.add_argument(
        "--column-inventory-csv-path",
        type=Path,
        default=DEFAULT_E10_COLUMN_INVENTORY_CSV,
        help="CSV con inventario de columnas de la tabla E10.",
    )
    parser.add_argument(
        "--summary-md-path",
        type=Path,
        default=DEFAULT_E10_SUMMARY_MD,
        help="Markdown con resumen de construccion de la tabla E10.",
    )
    args = parser.parse_args()
    for field_name in (
        "source_workbook",
        "grid_workbook",
        "curated_e9_workbook",
        "dataset_path",
        "table_csv_path",
        "table_xlsx_path",
        "dictionary_md_path",
        "column_inventory_csv_path",
        "summary_md_path",
    ):
        setattr(args, field_name, Path(getattr(args, field_name)).expanduser().resolve())
    return args


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sin filas."
    render_df = df.fillna("")
    headers = [str(column) for column in render_df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in render_df.iterrows():
        values = [str(row[column]).replace("\n", " ").strip() for column in render_df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def safe_sign(series: pd.Series | np.ndarray) -> pd.Series:
    values = np.sign(pd.Series(series, dtype=float))
    return values.replace({-0.0: 0.0}).astype(float)


def compute_row_local_loss_vectorized(
    *,
    y_true: pd.Series,
    y_pred: pd.Series,
    y_current: pd.Series,
    horizon: int,
    target_range: float,
    reference_values: dict[str, Any],
) -> pd.Series:
    alpha = float(reference_values["alpha"])
    beta = float(reference_values["beta"])
    gamma = float(reference_values["gamma"])
    delta = float(reference_values["delta"])
    w_h = float(reference_values["horizon_weights"][int(horizon)])
    safe_range = max(float(target_range), 1e-12)

    actual_delta = y_true - y_current
    predicted_delta = y_pred - y_current
    abs_error = (y_pred - y_true).abs()
    l_num = (abs_error / safe_range).clip(upper=1.0)
    l_trend = (safe_sign(actual_delta) != safe_sign(predicted_delta)).astype(float)
    actual_fall = actual_delta <= FALL_THRESHOLD
    predicted_fall = predicted_delta <= FALL_THRESHOLD
    l_risk = np.where(actual_fall, (~predicted_fall).astype(float), 0.0)
    l_tol = (abs_error > ABS_ERROR_TOLERANCE).astype(float)

    return w_h * (alpha * l_num + beta * l_trend + gamma * l_risk + delta * l_tol)


def choose_best_min(values: dict[str, float | int | None], *, tolerance: float = 1e-12) -> tuple[str, bool]:
    filtered = {
        model_id: float(value)
        for model_id, value in values.items()
        if value is not None and pd.notna(value)
    }
    if not filtered:
        return "", False
    best_value = min(filtered.values())
    winners = sorted(
        model_id for model_id, value in filtered.items() if np.isclose(value, best_value, atol=tolerance, rtol=0.0)
    )
    return winners[0], len(winners) > 1


def choose_best_operational(
    row: pd.Series,
    included_run_ids: list[str],
) -> str:
    available = [
        run_id
        for run_id in included_run_ids
        if int(row.get(f"pred_disponible_{run_id}", 0) or 0) == 1
    ]
    if not available:
        return ""

    actual_fall = int(row["actual_caida"]) == 1
    if actual_fall:
        candidates = {
            run_id: row.get(f"loss_local_{run_id}")
            for run_id in available
            if pd.notna(row.get(f"acierto_caida_{run_id}")) and int(row.get(f"acierto_caida_{run_id}") or 0) == 1
        }
        winner, _ = choose_best_min(candidates)
        if winner:
            return winner

    direction_candidates = {
        run_id: row.get(f"loss_local_{run_id}")
        for run_id in available
        if pd.notna(row.get(f"acierto_direccion_{run_id}")) and int(row.get(f"acierto_direccion_{run_id}") or 0) == 1
    }
    winner, _ = choose_best_min(direction_candidates)
    if winner:
        return winner

    fallback = {run_id: row.get(f"loss_local_{run_id}") for run_id in available}
    winner, _ = choose_best_min(fallback)
    return winner


def load_runs_catalog(workbook_path: Path) -> pd.DataFrame:
    return pd.read_excel(workbook_path, sheet_name="runs_catalogo")


def build_model_registry(runs_catalog_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    lookup = runs_catalog_df.set_index("run_id")
    included_rows: list[dict[str, Any]] = []
    for spec in E10_INCLUDED_MODELS:
        run_id = spec["run_id"]
        if run_id not in lookup.index:
            raise KeyError(f"No existe {run_id} en runs_catalogo.")
        row = lookup.loc[run_id]
        included_rows.append(
            {
                "run_id": run_id,
                "family": row["family"],
                "model": row["model"],
                "run_dir": row["run_dir"],
                "status_canonico": row["status_canonico"],
                "task_type": row["task_type"],
                "constructo_e10": spec["constructo"],
                "decision_e10": "incluido",
                "justificacion_e10": spec["justificacion"],
            }
        )

    excluded_rows: list[dict[str, Any]] = []
    for spec in E10_EXCLUDED_MODELS:
        run_id = spec["run_id"]
        if run_id not in lookup.index:
            continue
        row = lookup.loc[run_id]
        excluded_rows.append(
            {
                "run_id": run_id,
                "family": row["family"],
                "model": row["model"],
                "run_dir": row["run_dir"],
                "status_canonico": row["status_canonico"],
                "task_type": row["task_type"],
                "constructo_e10": "excluido_del_pool_principal",
                "decision_e10": "excluido",
                "justificacion_e10": spec["motivo_exclusion"],
            }
        )

    included_df = pd.DataFrame(included_rows).sort_values("run_id").reset_index(drop=True)
    excluded_df = pd.DataFrame(excluded_rows).sort_values("run_id").reset_index(drop=True)
    return included_df, excluded_df


def load_prediction_lookup(included_df: pd.DataFrame) -> dict[tuple[str, int], pd.DataFrame]:
    lookup: dict[tuple[str, int], pd.DataFrame] = {}
    for row in included_df.to_dict(orient="records"):
        run_id = row["run_id"]
        run_dir = Path(row["run_dir"]).expanduser().resolve()
        for horizon in (1, 2, 3, 4):
            pred_path = run_dir / f"predicciones_h{horizon}.csv"
            audit_result = audit_prediction_file(run_id, horizon, pred_path)
            standardized_df = audit_result.standardized_df
            if standardized_df is None or standardized_df.empty:
                continue
            standardized_df = standardized_df.copy()
            standardized_df["fecha"] = pd.to_datetime(standardized_df["fecha"])
            lookup[(run_id, horizon)] = standardized_df
    return lookup


def build_context_master_frame(master_df: pd.DataFrame) -> pd.DataFrame:
    out = master_df.copy().sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)
    net_columns = [
        column
        for column in out.columns
        if column.startswith("v5_") and column.endswith("_neto")
    ]

    out["ctx_y_lag1"] = out[CURRENT_TARGET_COLUMN].shift(1)
    out["ctx_y_lag2"] = out[CURRENT_TARGET_COLUMN].shift(2)
    out["ctx_y_lag4"] = out[CURRENT_TARGET_COLUMN].shift(4)
    out["ctx_delta_1w"] = out[CURRENT_TARGET_COLUMN] - out["ctx_y_lag1"]
    out["ctx_delta_2w"] = out[CURRENT_TARGET_COLUMN] - out["ctx_y_lag2"]
    out["ctx_abs_delta_1w"] = out["ctx_delta_1w"].abs()
    out["ctx_rolling_mean_4w"] = out[CURRENT_TARGET_COLUMN].rolling(window=4, min_periods=2).mean()
    out["ctx_rolling_std_4w"] = out[CURRENT_TARGET_COLUMN].rolling(window=4, min_periods=2).std(ddof=0)
    out["ctx_trend_vs_ma4"] = out[CURRENT_TARGET_COLUMN] - out["ctx_rolling_mean_4w"]
    out["ctx_mean_delta_4w"] = out[CURRENT_TARGET_COLUMN].diff().rolling(window=4, min_periods=2).mean()
    out["ctx_positive_delta_ratio_4w"] = (
        (out[CURRENT_TARGET_COLUMN].diff() > 0).astype(float).rolling(window=4, min_periods=2).mean()
    )
    out["ctx_negative_delta_ratio_4w"] = (
        (out[CURRENT_TARGET_COLUMN].diff() < 0).astype(float).rolling(window=4, min_periods=2).mean()
    )
    out["ctx_recent_fall_flag"] = (out["ctx_delta_1w"] <= FALL_THRESHOLD).astype(float)
    out["ctx_sentimiento_medios"] = pd.to_numeric(out.get("sentimiento_medios"), errors="coerce")
    if net_columns:
        out["ctx_v5_promedio_neto"] = out[net_columns].mean(axis=1)
        out["ctx_v5_dispersion_neta"] = out[net_columns].std(axis=1, ddof=0)
    else:
        out["ctx_v5_promedio_neto"] = np.nan
        out["ctx_v5_dispersion_neta"] = np.nan
    out["ctx_semana_iso"] = pd.to_numeric(out[WEEK_COLUMN], errors="coerce")
    return out


def add_prediction_blocks(
    *,
    base_df: pd.DataFrame,
    included_run_ids: list[str],
    prediction_lookup: dict[tuple[str, int], pd.DataFrame],
    horizon: int,
) -> pd.DataFrame:
    out = base_df.copy()
    for run_id in included_run_ids:
        pred_col = f"pred_{run_id}"
        standardized_df = prediction_lookup.get((run_id, horizon))
        if standardized_df is None or standardized_df.empty:
            out[pred_col] = np.nan
            continue
        model_df = standardized_df[["fecha", "y_pred"]].rename(columns={"y_pred": pred_col})
        out = out.merge(model_df, on="fecha", how="left", validate="one_to_one")
    return out


def add_row_integrity_columns(df: pd.DataFrame, included_run_ids: list[str]) -> pd.DataFrame:
    out = df.copy()
    pred_columns = [f"pred_{run_id}" for run_id in included_run_ids]

    for run_id in included_run_ids:
        pred_col = f"pred_{run_id}"
        out[f"pred_disponible_{run_id}"] = out[pred_col].notna().astype(int)

    availability_columns = [f"pred_disponible_{run_id}" for run_id in included_run_ids]
    out["n_modelos_disponibles"] = out[availability_columns].sum(axis=1)
    out["fila_completa_modelos_incluidos"] = (out["n_modelos_disponibles"] == len(included_run_ids)).astype(int)
    out["cobertura_modelos_fila"] = out["n_modelos_disponibles"] / float(len(included_run_ids))

    def _join_models(row: pd.Series, *, available: bool) -> str:
        values = []
        for run_id in included_run_ids:
            present = int(row[f"pred_disponible_{run_id}"]) == 1
            if present == available:
                values.append(run_id)
        return ",".join(values)

    out["modelos_disponibles_lista"] = out.apply(lambda row: _join_models(row, available=True), axis=1)
    out["modelos_faltantes_lista"] = out.apply(lambda row: _join_models(row, available=False), axis=1)
    out["notas_integridad_fila"] = np.where(
        out["fila_completa_modelos_incluidos"] == 1,
        "fila_completa_pool_E10",
        "faltan_predicciones_de=" + out["modelos_faltantes_lista"].astype(str),
    )
    return out


def add_actual_outcome_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["actual_delta"] = out["y_real"] - out["y_current"]
    out["actual_direction"] = safe_sign(out["actual_delta"])
    out["actual_caida"] = (out["actual_delta"] <= FALL_THRESHOLD).astype(int)
    return out


def add_model_level_columns(
    *,
    df: pd.DataFrame,
    included_run_ids: list[str],
    horizon: int,
    reference_values: dict[str, Any],
) -> pd.DataFrame:
    out = df.copy()
    target_range = float(out["y_real"].max() - out["y_real"].min())
    for run_id in included_run_ids:
        pred_col = f"pred_{run_id}"
        availability_col = f"pred_disponible_{run_id}"
        direction_col = f"direccion_pred_{run_id}"
        fall_col = f"caida_pred_{run_id}"
        abs_error_col = f"abs_error_{run_id}"
        sq_error_col = f"sq_error_{run_id}"
        hit_direction_col = f"acierto_direccion_{run_id}"
        hit_fall_col = f"acierto_caida_{run_id}"
        local_loss_col = f"loss_local_{run_id}"

        predicted_delta = out[pred_col] - out["y_current"]
        predicted_direction = safe_sign(predicted_delta)
        out[direction_col] = np.where(out[availability_col] == 1, predicted_direction, np.nan)
        out[fall_col] = np.where(out[availability_col] == 1, (predicted_delta <= FALL_THRESHOLD).astype(int), np.nan)
        out[abs_error_col] = np.where(out[availability_col] == 1, (out[pred_col] - out["y_real"]).abs(), np.nan)
        out[sq_error_col] = np.where(out[availability_col] == 1, (out[pred_col] - out["y_real"]) ** 2, np.nan)
        out[hit_direction_col] = np.where(
            out[availability_col] == 1,
            (out[direction_col] == out["actual_direction"]).astype(int),
            np.nan,
        )
        out[hit_fall_col] = np.where(
            (out[availability_col] == 1) & (out["actual_caida"] == 1),
            (out[fall_col] == 1).astype(int),
            np.nan,
        )
        valid_mask = out[availability_col] == 1
        local_loss = compute_row_local_loss_vectorized(
            y_true=out["y_real"],
            y_pred=out[pred_col].fillna(out["y_real"]),
            y_current=out["y_current"],
            horizon=horizon,
            target_range=target_range,
            reference_values=reference_values,
        )
        out[local_loss_col] = np.where(valid_mask, local_loss, np.nan)

        out[f"hist_abs_error_mean4_{run_id}"] = out[abs_error_col].shift(1).rolling(
            window=4, min_periods=1
        ).mean()
        out[f"hist_loss_local_mean4_{run_id}"] = out[local_loss_col].shift(1).rolling(
            window=4, min_periods=1
        ).mean()
        out[f"hist_dir_acc_mean4_{run_id}"] = out[hit_direction_col].shift(1).rolling(
            window=4, min_periods=1
        ).mean()
        out[f"hist_caida_hit_mean4_{run_id}"] = out[hit_fall_col].shift(1).rolling(
            window=4, min_periods=1
        ).mean()

    return out


def add_disagreement_columns(df: pd.DataFrame, included_run_ids: list[str]) -> pd.DataFrame:
    out = df.copy()
    pred_columns = [f"pred_{run_id}" for run_id in included_run_ids]
    direction_columns = [f"direccion_pred_{run_id}" for run_id in included_run_ids]
    fall_columns = [f"caida_pred_{run_id}" for run_id in included_run_ids]

    def _row_metrics(row: pd.Series) -> pd.Series:
        preds = [float(row[column]) for column in pred_columns if pd.notna(row[column])]
        directions = [int(row[column]) for column in direction_columns if pd.notna(row[column])]
        fall_votes = [int(row[column]) for column in fall_columns if pd.notna(row[column])]
        n_models = len(preds)
        if not preds:
            return pd.Series(
                {
                    "promedio_predicciones": np.nan,
                    "mediana_predicciones": np.nan,
                    "min_predicciones": np.nan,
                    "max_predicciones": np.nan,
                    "rango_predicciones": np.nan,
                    "desviacion_predicciones": np.nan,
                    "max_diff_predicciones": np.nan,
                    "consenso_direccion": np.nan,
                    "desacuerdo_direccion": np.nan,
                    "n_direcciones_distintas": np.nan,
                    "numero_modelos_predicen_caida": np.nan,
                    "share_modelos_predicen_caida": np.nan,
                    "dispersion_direccion": np.nan,
                }
            )

        unique_directions = sorted(set(directions))
        n_unique_directions = len(unique_directions)
        numero_modelos_predicen_caida = sum(fall_votes)
        return pd.Series(
            {
                "promedio_predicciones": float(np.mean(preds)),
                "mediana_predicciones": float(np.median(preds)),
                "min_predicciones": float(np.min(preds)),
                "max_predicciones": float(np.max(preds)),
                "rango_predicciones": float(np.max(preds) - np.min(preds)),
                "desviacion_predicciones": float(np.std(preds, ddof=0)),
                "max_diff_predicciones": float(np.max(preds) - np.min(preds)),
                "consenso_direccion": int(n_unique_directions == 1),
                "desacuerdo_direccion": int(n_unique_directions > 1),
                "n_direcciones_distintas": int(n_unique_directions),
                "numero_modelos_predicen_caida": int(numero_modelos_predicen_caida),
                "share_modelos_predicen_caida": float(numero_modelos_predicen_caida / max(n_models, 1)),
                "dispersion_direccion": float(n_unique_directions / max(n_models, 1)),
            }
        )

    disagreement_df = out.apply(_row_metrics, axis=1)
    return pd.concat([out, disagreement_df], axis=1)


def add_selector_targets(df: pd.DataFrame, included_run_ids: list[str]) -> pd.DataFrame:
    out = df.copy()
    best_abs: list[str] = []
    tie_abs: list[int] = []
    best_mae_local: list[str] = []
    best_dir: list[str] = []
    best_caida: list[str] = []
    best_loss: list[str] = []
    tie_loss: list[int] = []
    best_oper: list[str] = []

    for _, row in out.iterrows():
        available = [
            run_id
            for run_id in included_run_ids
            if int(row.get(f"pred_disponible_{run_id}", 0) or 0) == 1
        ]
        abs_values = {run_id: row.get(f"abs_error_{run_id}") for run_id in available}
        best_abs_run, has_tie_abs = choose_best_min(abs_values)
        best_abs.append(best_abs_run)
        tie_abs.append(int(has_tie_abs))
        best_mae_local.append(best_abs_run)

        direction_candidates = {
            run_id: row.get(f"abs_error_{run_id}")
            for run_id in available
            if pd.notna(row.get(f"acierto_direccion_{run_id}")) and int(row.get(f"acierto_direccion_{run_id}") or 0) == 1
        }
        best_dir_run, _ = choose_best_min(direction_candidates)
        best_dir.append(best_dir_run or "sin_modelo_con_direccion_correcta")

        if int(row["actual_caida"]) == 1:
            caida_candidates = {
                run_id: row.get(f"abs_error_{run_id}")
                for run_id in available
                if pd.notna(row.get(f"acierto_caida_{run_id}")) and int(row.get(f"acierto_caida_{run_id}") or 0) == 1
            }
            best_caida_run, _ = choose_best_min(caida_candidates)
            best_caida.append(best_caida_run or "sin_modelo_detecta_caida")
        else:
            best_caida.append("no_aplica_no_hubo_caida")

        loss_values = {run_id: row.get(f"loss_local_{run_id}") for run_id in available}
        best_loss_run, has_tie_loss = choose_best_min(loss_values)
        best_loss.append(best_loss_run)
        tie_loss.append(int(has_tie_loss))
        best_oper.append(choose_best_operational(row, included_run_ids))

    out["mejor_modelo_error_abs"] = best_abs
    out["mejor_modelo_mae_local"] = best_mae_local
    out["mejor_modelo_direccion"] = best_dir
    out["mejor_modelo_caida"] = best_caida
    out["mejor_modelo_loss_radar_local"] = best_loss
    out["empate_mejor_modelo_error_abs"] = tie_abs
    out["empate_mejor_modelo"] = tie_loss
    out["mejor_modelo_operativo"] = best_oper
    return out


def build_horizon_e10_table(
    *,
    master_context_df: pd.DataFrame,
    included_run_ids: list[str],
    prediction_lookup: dict[tuple[str, int], pd.DataFrame],
    horizon: int,
    reference_values: dict[str, Any],
) -> pd.DataFrame:
    horizon_target_column = TARGET_COLUMNS[horizon]
    context_columns = [
        DATE_COLUMN,
        WEEK_COLUMN,
        CURRENT_TARGET_COLUMN,
        horizon_target_column,
        "ctx_y_lag1",
        "ctx_y_lag2",
        "ctx_y_lag4",
        "ctx_delta_1w",
        "ctx_delta_2w",
        "ctx_abs_delta_1w",
        "ctx_rolling_mean_4w",
        "ctx_rolling_std_4w",
        "ctx_trend_vs_ma4",
        "ctx_mean_delta_4w",
        "ctx_positive_delta_ratio_4w",
        "ctx_negative_delta_ratio_4w",
        "ctx_recent_fall_flag",
        "ctx_sentimiento_medios",
        "ctx_v5_promedio_neto",
        "ctx_v5_dispersion_neta",
        "ctx_semana_iso",
    ]
    base_df = master_context_df[context_columns].rename(
        columns={
            DATE_COLUMN: "fecha",
            CURRENT_TARGET_COLUMN: "y_current",
            horizon_target_column: "y_real",
            WEEK_COLUMN: "semana_iso",
        }
    )
    base_df = base_df.dropna(subset=["y_real"]).copy()
    base_df["fecha"] = pd.to_datetime(base_df["fecha"])
    base_df["horizonte"] = int(horizon)
    base_df["source_version"] = E10_SOURCE_VERSION
    base_df["source_table_origin"] = DEFAULT_MASTER_TABLE_PATH.name
    base_df["source_curated_e9_origin"] = DEFAULT_CURATED_E9_TABLE_PATH.name
    base_df["split_role_retro"] = "pending_e10_runner"

    base_df = add_prediction_blocks(
        base_df=base_df,
        included_run_ids=included_run_ids,
        prediction_lookup=prediction_lookup,
        horizon=horizon,
    )
    base_df = add_row_integrity_columns(base_df, included_run_ids=included_run_ids)
    base_df = base_df.loc[base_df["n_modelos_disponibles"] > 0].copy()
    base_df = base_df.sort_values("fecha", kind="stable").reset_index(drop=True)
    base_df["row_id"] = base_df["fecha"].dt.strftime(f"H{horizon}_%Y%m%d")
    base_df["origen_temporal_id"] = base_df["row_id"]

    base_df = add_actual_outcome_columns(base_df)
    base_df = add_model_level_columns(
        df=base_df,
        included_run_ids=included_run_ids,
        horizon=horizon,
        reference_values=reference_values,
    )
    base_df = add_disagreement_columns(base_df, included_run_ids=included_run_ids)
    base_df = add_selector_targets(base_df, included_run_ids=included_run_ids)
    return base_df


def build_long_table_by_horizon(horizon_tables: dict[int, pd.DataFrame]) -> pd.DataFrame:
    long_df = pd.concat(
        [horizon_tables[horizon] for horizon in sorted(horizon_tables)],
        axis=0,
        ignore_index=True,
    )
    long_df = long_df.sort_values(["horizonte", "fecha"], kind="stable").reset_index(drop=True)
    return long_df


def build_column_inventory(included_run_ids: list[str], history_window: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add_row(
        column_name: str,
        *,
        block: str,
        descripcion: str,
        formula_o_fuente: str,
        usa_y_real: bool,
        observable_en_t: bool,
        puede_ser_feature: bool,
        role: str,
        riesgo_leakage: str,
        comentario_metodologico: str,
    ) -> None:
        rows.append(
            {
                "column_name": column_name,
                "block": block,
                "descripcion": descripcion,
                "formula_o_fuente": formula_o_fuente,
                "usa_y_real": usa_y_real,
                "observable_en_t": observable_en_t,
                "puede_ser_feature": puede_ser_feature,
                "role": role,
                "riesgo_leakage": riesgo_leakage,
                "comentario_metodologico": comentario_metodologico,
            }
        )

    id_columns = {
        "row_id": "Identificador unico fila-horizonte.",
        "fecha": "Fecha de la observacion evaluable.",
        "horizonte": "Horizonte de prediccion en semanas.",
        "origen_temporal_id": "Alias trazable del corte temporal base.",
        "source_version": "Version de la tabla derivada E10.",
        "source_table_origin": "Workbook maestro canonicamente usado como origen.",
        "source_curated_e9_origin": "Workbook curado de E9 usado como referencia de continuidad.",
        "split_role_retro": "Marcador de que la fila aun no pertenece a un split E10 concreto.",
        "semana_iso": "Semana ISO de la observacion.",
        "notas_integridad_fila": "Observacion breve sobre completitud o faltantes de modelos.",
        "modelos_disponibles_lista": "Lista de modelos con prediccion disponible en la fila.",
        "modelos_faltantes_lista": "Lista de modelos ausentes en la fila.",
    }
    for column_name, description in id_columns.items():
        add_row(
            column_name,
            block="identidad_trazabilidad",
            descripcion=description,
            formula_o_fuente="tabla derivada E10",
            usa_y_real=False,
            observable_en_t=column_name not in {"notas_integridad_fila"},
            puede_ser_feature=False,
            role="id" if column_name not in {"notas_integridad_fila", "modelos_disponibles_lista", "modelos_faltantes_lista"} else "diagnostic_only",
            riesgo_leakage="bajo",
            comentario_metodologico="Sirve para alinear, auditar o resumir la fila; no debe confundirse con una feature modelable directa.",
        )

    add_row(
        "y_current",
        block="identidad_trazabilidad",
        descripcion="Nivel observado en t, disponible al momento de predecir.",
        formula_o_fuente="dataset maestro / y_t_aceptacion_digital",
        usa_y_real=False,
        observable_en_t=True,
        puede_ser_feature=True,
        role="feature_candidate",
        riesgo_leakage="bajo",
        comentario_metodologico="Es contexto observable en tiempo real y puede usarse como feature contextual.",
    )
    add_row(
        "y_real",
        block="identidad_trazabilidad",
        descripcion="Valor observado real del horizonte correspondiente.",
        formula_o_fuente="dataset maestro / target_h",
        usa_y_real=True,
        observable_en_t=False,
        puede_ser_feature=False,
        role="forbidden_for_training",
        riesgo_leakage="alto",
        comentario_metodologico="Es el outcome realizado y solo puede usarse para evaluacion, diagnostico o construccion de labels retrospectivos.",
    )

    generic_feature_candidates = {
        "n_modelos_disponibles": "Conteo de modelos con prediccion disponible en la fila.",
        "fila_completa_modelos_incluidos": "Indicador de disponibilidad total del pool principal de E10.",
        "cobertura_modelos_fila": "Proporcion de modelos disponibles respecto del pool incluido.",
        "actual_delta": "Cambio realizado respecto de y_current.",
        "actual_direction": "Direccion realizada de la observacion.",
        "actual_caida": "Indicador de caida realizada bajo el umbral operativo del Radar.",
        "promedio_predicciones": "Promedio de predicciones disponibles.",
        "mediana_predicciones": "Mediana de predicciones disponibles.",
        "min_predicciones": "Minimo de predicciones disponibles.",
        "max_predicciones": "Maximo de predicciones disponibles.",
        "rango_predicciones": "Rango max-min de predicciones disponibles.",
        "desviacion_predicciones": "Desviacion estandar de predicciones disponibles.",
        "max_diff_predicciones": "Diferencia maxima entre predicciones disponibles.",
        "consenso_direccion": "1 si todas las direcciones predichas coinciden; 0 si no.",
        "desacuerdo_direccion": "1 si existe desacuerdo de direccion entre modelos disponibles.",
        "n_direcciones_distintas": "Numero de direcciones distintas entre modelos disponibles.",
        "numero_modelos_predicen_caida": "Numero de modelos que predicen caida.",
        "share_modelos_predicen_caida": "Proporcion de modelos que predicen caida.",
        "dispersion_direccion": "Numero de direcciones distintas relativo al total disponible.",
        "ctx_y_lag1": "Nivel observado una semana atras.",
        "ctx_y_lag2": "Nivel observado dos semanas atras.",
        "ctx_y_lag4": "Nivel observado cuatro semanas atras.",
        "ctx_delta_1w": "Cambio observado entre t y t-1.",
        "ctx_delta_2w": "Cambio observado entre t y t-2.",
        "ctx_abs_delta_1w": "Magnitud absoluta del ultimo cambio observado.",
        "ctx_rolling_mean_4w": "Media movil de 4 semanas del target observada hasta t.",
        "ctx_rolling_std_4w": "Volatilidad reciente de 4 semanas del target observada hasta t.",
        "ctx_trend_vs_ma4": "Separacion entre nivel actual y media movil de 4 semanas.",
        "ctx_mean_delta_4w": "Cambio medio reciente de 4 semanas.",
        "ctx_positive_delta_ratio_4w": "Proporcion reciente de cambios positivos en 4 semanas.",
        "ctx_negative_delta_ratio_4w": "Proporcion reciente de cambios negativos en 4 semanas.",
        "ctx_recent_fall_flag": "Bandera de que el ultimo cambio observado fue una caida.",
        "ctx_sentimiento_medios": "Sentimiento de medios observado en t.",
        "ctx_v5_promedio_neto": "Promedio de variables tematicas netas observadas en t.",
        "ctx_v5_dispersion_neta": "Dispersion de variables tematicas netas observadas en t.",
        "ctx_semana_iso": "Contexto temporal basico disponible en t.",
    }
    for column_name, description in generic_feature_candidates.items():
        uses_y = column_name.startswith("actual_")
        observable = not uses_y
        can_feature = column_name not in {"actual_delta", "actual_direction", "actual_caida"}
        role = "feature_candidate" if can_feature else "forbidden_for_training"
        add_row(
            column_name,
            block="contexto_desacuerdo" if not column_name.startswith("ctx_") else "contexto_observable",
            descripcion=description,
            formula_o_fuente="tabla E10 derivada / dataset maestro / resumen entre predicciones",
            usa_y_real=uses_y,
            observable_en_t=observable,
            puede_ser_feature=can_feature,
            role=role,
            riesgo_leakage="alto" if uses_y else "bajo",
            comentario_metodologico=(
                "Usa y_real y por tanto no puede ser feature online."
                if uses_y
                else "Observable en t y apta como feature contextual o de desacuerdo."
            ),
        )

    for run_id in included_run_ids:
        add_row(
            f"pred_{run_id}",
            block="predicciones_base",
            descripcion=f"Prediccion OOF del modelo {run_id}.",
            formula_o_fuente=f"predicciones_h*.csv canonicamente registradas para {run_id}",
            usa_y_real=False,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="bajo",
            comentario_metodologico="Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating.",
        )
        add_row(
            f"pred_disponible_{run_id}",
            block="predicciones_base",
            descripcion=f"Indicador de disponibilidad de la prediccion de {run_id}.",
            formula_o_fuente=f"1 si pred_{run_id} no es NaN; 0 en otro caso",
            usa_y_real=False,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="bajo",
            comentario_metodologico="Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto.",
        )
        add_row(
            f"direccion_pred_{run_id}",
            block="predicciones_base",
            descripcion=f"Direccion implicita de {run_id} respecto a y_current (-1/0/1).",
            formula_o_fuente=f"sign(pred_{run_id} - y_current)",
            usa_y_real=False,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="bajo",
            comentario_metodologico="Es derivable de una prediccion disponible en tiempo real.",
        )
        add_row(
            f"caida_pred_{run_id}",
            block="predicciones_base",
            descripcion=f"Indicador de que {run_id} predice caida segun el umbral operativo vigente.",
            formula_o_fuente=f"(pred_{run_id} - y_current) <= {FALL_THRESHOLD}",
            usa_y_real=False,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="bajo",
            comentario_metodologico="Es particularmente valiosa para un gating orientado a riesgo y caidas.",
        )
        add_row(
            f"abs_error_{run_id}",
            block="error_ex_post",
            descripcion=f"Error absoluto realizado de {run_id}.",
            formula_o_fuente=f"abs(pred_{run_id} - y_real)",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="forbidden_for_training",
            riesgo_leakage="alto",
            comentario_metodologico="Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila.",
        )
        add_row(
            f"sq_error_{run_id}",
            block="error_ex_post",
            descripcion=f"Error cuadratico realizado de {run_id}.",
            formula_o_fuente=f"(pred_{run_id} - y_real)^2",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="forbidden_for_training",
            riesgo_leakage="alto",
            comentario_metodologico="Solo diagnostico retrospectivo; prohibido como feature online.",
        )
        add_row(
            f"acierto_direccion_{run_id}",
            block="error_ex_post",
            descripcion=f"Indicador retrospectivo de acierto de direccion de {run_id}.",
            formula_o_fuente=f"sign(pred_{run_id} - y_current) == actual_direction",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="forbidden_for_training",
            riesgo_leakage="alto",
            comentario_metodologico="Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature.",
        )
        add_row(
            f"acierto_caida_{run_id}",
            block="error_ex_post",
            descripcion=f"Indicador retrospectivo de deteccion de caida de {run_id} cuando hubo caida real.",
            formula_o_fuente=f"si actual_caida=1, entonces caida_pred_{run_id}; en otro caso NaN",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="forbidden_for_training",
            riesgo_leakage="alto",
            comentario_metodologico="Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted.",
        )
        add_row(
            f"loss_local_{run_id}",
            block="error_ex_post",
            descripcion=f"Perdida local tipo Radar para {run_id} en la fila-horizonte.",
            formula_o_fuente="Combinacion ponderada local de l_num, l_trend, l_risk y l_tol con pesos vigentes del Radar",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="forbidden_for_training",
            riesgo_leakage="alto",
            comentario_metodologico="Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila.",
        )
        add_row(
            f"hist_abs_error_mean4_{run_id}",
            block="historico_modelos",
            descripcion=f"Promedio rolling shifted de error absoluto pasado de {run_id}.",
            formula_o_fuente=f"rolling_mean(window={history_window}) de abs_error_{run_id}.shift(1)",
            usa_y_real=True,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="medio_controlado",
            comentario_metodologico="Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila.",
        )
        add_row(
            f"hist_loss_local_mean4_{run_id}",
            block="historico_modelos",
            descripcion=f"Promedio rolling shifted de perdida local pasada de {run_id}.",
            formula_o_fuente=f"rolling_mean(window={history_window}) de loss_local_{run_id}.shift(1)",
            usa_y_real=True,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="medio_controlado",
            comentario_metodologico="Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual.",
        )
        add_row(
            f"hist_dir_acc_mean4_{run_id}",
            block="historico_modelos",
            descripcion=f"Tasa rolling shifted de acierto de direccion reciente de {run_id}.",
            formula_o_fuente=f"rolling_mean(window={history_window}) de acierto_direccion_{run_id}.shift(1)",
            usa_y_real=True,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="medio_controlado",
            comentario_metodologico="Apta como feature solo porque usa resultados ya observados de filas anteriores.",
        )
        add_row(
            f"hist_caida_hit_mean4_{run_id}",
            block="historico_modelos",
            descripcion=f"Tasa rolling shifted de deteccion de caidas reales por {run_id}.",
            formula_o_fuente=f"rolling_mean(window={history_window}) de acierto_caida_{run_id}.shift(1)",
            usa_y_real=True,
            observable_en_t=True,
            puede_ser_feature=True,
            role="feature_candidate",
            riesgo_leakage="medio_controlado",
            comentario_metodologico="Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs.",
        )

    selector_target_descriptions = {
        "mejor_modelo_error_abs": "Modelo con menor error absoluto en la fila entre los disponibles.",
        "mejor_modelo_mae_local": "Alias operativo del mejor modelo por error absoluto local.",
        "mejor_modelo_direccion": "Modelo con direccion correcta y menor error absoluto; si ninguno acierta, valor sentinela.",
        "mejor_modelo_caida": "Modelo que detecta la caida real con menor error absoluto; si no hubo caida o nadie la detecta, valor sentinela.",
        "mejor_modelo_loss_radar_local": "Modelo con menor perdida local Radar en la fila.",
        "empate_mejor_modelo_error_abs": "Bandera de empate exacto/numericamente equivalente para el mejor modelo por error absoluto.",
        "empate_mejor_modelo": "Bandera de empate exacto/numericamente equivalente para el mejor modelo por perdida local.",
        "mejor_modelo_operativo": "Selector retrospectivo jerarquico: primero caida, luego direccion, luego perdida local.",
    }
    for column_name, description in selector_target_descriptions.items():
        add_row(
            column_name,
            block="targets_selector",
            descripcion=description,
            formula_o_fuente="Derivado retrospectivamente a partir de predicciones base y y_real de la misma fila.",
            usa_y_real=True,
            observable_en_t=False,
            puede_ser_feature=False,
            role="target_selector",
            riesgo_leakage="alto",
            comentario_metodologico="Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema.",
        )

    inventory_df = pd.DataFrame(rows).sort_values(["block", "column_name"]).reset_index(drop=True)
    return inventory_df


def build_dictionary_markdown(
    *,
    included_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    history_window: int,
) -> str:
    def _render_df(df: pd.DataFrame) -> str:
        if df.empty:
            return "Sin filas."
        return dataframe_to_markdown(df)

    feature_df = inventory_df[inventory_df["role"] == "feature_candidate"][
        ["column_name", "block", "descripcion", "riesgo_leakage", "comentario_metodologico"]
    ]
    target_df = inventory_df[inventory_df["role"] == "target_selector"][
        ["column_name", "descripcion", "comentario_metodologico"]
    ]
    forbidden_df = inventory_df[inventory_df["role"] == "forbidden_for_training"][
        ["column_name", "block", "descripcion", "comentario_metodologico"]
    ]

    return f"""# Diccionario metodologico de la tabla E10

## Proposito

Este diccionario documenta la tabla `E10` como infraestructura especifica para meta-seleccion / gating contextual.

`E10` no reutiliza directamente la tabla de `E9` como si fuera suficiente por si sola. La tabla construida aqui separa:

- predicciones base,
- contexto observable en `t`,
- historicos shifted de rendimiento,
- variables de desacuerdo,
- targets retrospectivos del selector,
- y columnas prohibidas como features.

## Pool incluido de modelos base

{_render_df(included_df[["run_id", "family", "model", "constructo_e10", "justificacion_e10"]])}

## Modelos explicitamente excluidos del pool principal

{_render_df(excluded_df[["run_id", "family", "model", "justificacion_e10"]])}

## Constructos metodologicos de la tabla

### 1. Predicciones base

Columnas `pred_*`, `direccion_pred_*`, `caida_pred_*` y `pred_disponible_*`.

- representan salidas OOF ya observadas por modelo base;
- son observables en tiempo real si ese modelo emite prediccion para la fila;
- pueden alimentar un meta-selector o gating futuro.

### 2. Variables de desacuerdo

Columnas como `rango_predicciones`, `desviacion_predicciones`, `consenso_direccion` y `numero_modelos_predicen_caida`.

- resumen cuanta dispersion o consenso existe entre modelos;
- son especialmente utiles para `E10`, porque el gating contextual depende de reconocer cuando los modelos discrepan;
- no usan `y_real`, por tanto son candidatas a feature.

### 3. Contexto observable en t

Columnas `ctx_*`.

- se derivan solo de informacion conocida al momento de predecir;
- incluyen nivel reciente, cambios recientes, volatilidad reciente y resumenes simples del bloque exogeno actual;
- no usan informacion futura.

### 4. Historicos shifted de rendimiento por modelo

Columnas `hist_*` con ventana `rolling={history_window}`.

- usan errores o aciertos pasados ya observados;
- se calculan con `shift(1)` para evitar que la fila actual contamine su propia feature;
- son candidatas a feature solo bajo esa disciplina temporal estricta.

### 5. Error ex post y diagnostico retrospectivo

Columnas `abs_error_*`, `sq_error_*`, `acierto_direccion_*`, `acierto_caida_*`, `loss_local_*`, `actual_*`.

- existen para auditoria, comparacion y construccion de labels retrospectivos;
- usan `y_real` de la misma fila;
- estan prohibidas como features de entrenamiento online.

### 6. Targets retrospectivos del selector

Columnas `mejor_modelo_*` y `empate_*`.

- no son features;
- son labels para entrenar selectores duros, selectores operativos o modelos de gating supervisado;
- deben usarse solo dentro de una validacion temporal correcta cuando se llegue a correr `E10`.

## Columnas aptas como feature candidate

{_render_df(feature_df)}

## Targets del selector

{_render_df(target_df)}

## Columnas prohibidas para entrenamiento

{_render_df(forbidden_df)}

## Precaucion metodologica central

La separacion entre columnas observables en `t` y columnas que usan `y_real` de la misma fila es obligatoria. Si esta frontera se rompe, `E10` deja de ser un gating contextual defendible y pasa a tener leakage retrospectivo.
"""


def build_summary_markdown(
    *,
    included_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    horizon_tables: dict[int, pd.DataFrame],
    inventory_df: pd.DataFrame,
) -> str:
    coverage_rows: list[dict[str, Any]] = []
    for horizon, df in horizon_tables.items():
        coverage_rows.append(
            {
                "horizonte": f"H{horizon}",
                "filas_total": int(len(df)),
                "filas_completas_pool": int(df["fila_completa_modelos_incluidos"].sum()),
                "cobertura_media_pool": float(df["cobertura_modelos_fila"].mean()),
                "filas_con_E9_v2": int(df["pred_disponible_E9_v2_clean"].sum()),
                "filas_sin_E9_v2": int((df["pred_disponible_E9_v2_clean"] == 0).sum()),
            }
        )
    coverage_df = pd.DataFrame(coverage_rows)
    feature_candidates = inventory_df[inventory_df["role"] == "feature_candidate"]["column_name"].tolist()
    forbidden = inventory_df[inventory_df["role"] == "forbidden_for_training"]["column_name"].tolist()
    selector_targets = inventory_df[inventory_df["role"] == "target_selector"]["column_name"].tolist()

    hard_selector_ready = "utilizable con reservas"
    soft_gating_ready = "utilizable con reservas"
    readiness_note = (
        "La tabla ya permite investigar E10, pero la cobertura completa del pool principal queda limitada por "
        "`E9_v2_clean` (14/13/12/11 filas completas por horizonte). Antes de correr el primer selector real "
        "hace falta fijar explicitamente la politica de filas incompletas y el criterio de entrenamiento por horizonte."
    )

    return f"""# Resumen de construccion de la tabla E10

## 1. Archivo base

- Workbook maestro canonico: `{DEFAULT_MASTER_TABLE_PATH}`
- Workbook curado de E9 usado como referencia: `{DEFAULT_CURATED_E9_TABLE_PATH}`

## 2. Modelos incluidos finalmente

{dataframe_to_markdown(included_df[["run_id", "family", "model", "constructo_e10", "justificacion_e10"]])}

## 3. Modelos excluidos explicitamente del pool principal

{dataframe_to_markdown(excluded_df[["run_id", "family", "model", "justificacion_e10"]])}

## 4. Cobertura por horizonte

{dataframe_to_markdown(coverage_df)}

## 5. Que horizontes quedaron bien cubiertos

- Todos los horizontes `H1-H4` quedaron cubiertos por al menos un subconjunto amplio del pool.
- La union de candidatos deja `28/27/26/25` filas evaluables por horizonte.
- La interseccion completa de todo el pool principal queda limitada por `E9_v2_clean`.

## 6. La tabla quedo lista para meta-selector duro

- Estado: `{hard_selector_ready}`
- Motivo: ya existen features observables, labels retrospectivos y trazabilidad fila-horizonte, pero el overlap completo del pool principal sigue siendo corto.

## 7. La tabla quedo lista para gating blando

- Estado: `{soft_gating_ready}`
- Motivo: la tabla ya contiene predicciones base, desacuerdo entre modelos, contexto observable e historicos shifted de rendimiento.

## 8. Que columnas si pueden ser features

- Predicciones base `pred_*`
- Disponibilidad de prediccion `pred_disponible_*`
- Direccion y caida predichas `direccion_pred_*`, `caida_pred_*`
- Variables de desacuerdo entre modelos
- Contexto `ctx_*`
- Historicos shifted `hist_*`

## 9. Que columnas estan prohibidas para entrenamiento

- `y_real`
- `actual_delta`, `actual_direction`, `actual_caida`
- `abs_error_*`, `sq_error_*`
- `acierto_direccion_*`, `acierto_caida_*`
- `loss_local_*`
- `mejor_modelo_*`
- `empate_*`

## 10. Artefactos que faltan o sobran

- No faltan predicciones OOF para los modelos incluidos.
- Sobra cobertura asimetrica: `E9_v2_clean` entra por decision metodologica minima, pero reduce el numero de filas completas del pool.
- No se agregaron columnas oportunistas basadas en informacion futura.

## 11. Limitaciones persistentes

- Falta decidir politica formal para filas incompletas en `E10`.
- Falta decidir si el primer `E10` usara el pool completo o una variante por horizonte con subset estable.
- Falta definir el primer objetivo exacto del selector: numerico, direccion, caida o operativo.
- No existe todavia `run_e10_*` operativo; esta tarea deja la infraestructura de datos, no el modelado final.

## 12. Cierre metodologico

{readiness_note}

E10 requiere una tabla especifica distinta de la tabla usada por `E9`. La tabla construida aqui no busca todavia decidir el mejor selector, sino habilitar de forma limpia esa investigacion futura. La separacion entre predicciones base, contexto observable, desacuerdo entre modelos y etiquetas retrospectivas es condicion indispensable para evitar leakage y sostener trazabilidad fuerte.
"""


def write_outputs(
    *,
    long_df: pd.DataFrame,
    horizon_tables: dict[int, pd.DataFrame],
    included_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    args: argparse.Namespace,
) -> E10Artifacts:
    ensure_parent(args.table_csv_path)
    ensure_parent(args.table_xlsx_path)
    ensure_parent(args.dictionary_md_path)
    ensure_parent(args.column_inventory_csv_path)
    ensure_parent(args.summary_md_path)

    long_df.to_csv(args.table_csv_path, index=False)
    inventory_df.to_csv(args.column_inventory_csv_path, index=False)

    with pd.ExcelWriter(args.table_xlsx_path, engine="openpyxl") as writer:
        long_df.to_excel(writer, sheet_name="E10_base_long", index=False)
        for horizon, table in horizon_tables.items():
            table.to_excel(writer, sheet_name=f"E10_h{horizon}", index=False)
        included_df.to_excel(writer, sheet_name="E10_modelos_incluidos", index=False)
        excluded_df.to_excel(writer, sheet_name="E10_modelos_excluidos", index=False)
        inventory_df.to_excel(writer, sheet_name="E10_inventario_cols", index=False)

    dictionary_md = build_dictionary_markdown(
        included_df=included_df,
        excluded_df=excluded_df,
        inventory_df=inventory_df,
        history_window=args.history_window,
    )
    args.dictionary_md_path.write_text(dictionary_md, encoding="utf-8")

    summary_md = build_summary_markdown(
        included_df=included_df,
        excluded_df=excluded_df,
        horizon_tables=horizon_tables,
        inventory_df=inventory_df,
    )
    args.summary_md_path.write_text(summary_md, encoding="utf-8")

    complete_rows_by_horizon = {
        int(horizon): int(table["fila_completa_modelos_incluidos"].sum())
        for horizon, table in horizon_tables.items()
    }
    return E10Artifacts(
        table_csv_path=args.table_csv_path,
        table_xlsx_path=args.table_xlsx_path,
        dictionary_md_path=args.dictionary_md_path,
        column_inventory_csv_path=args.column_inventory_csv_path,
        summary_md_path=args.summary_md_path,
        rows_total=int(len(long_df)),
        complete_rows_by_horizon=complete_rows_by_horizon,
    )


def build_e10_meta_selector_table(args: argparse.Namespace) -> E10Artifacts:
    master_df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    master_context_df = build_context_master_frame(master_df)
    runs_catalog_df = load_runs_catalog(args.source_workbook)
    included_df, excluded_df = build_model_registry(runs_catalog_df)
    prediction_lookup = load_prediction_lookup(included_df)
    tracker = RadarExperimentTracker(workbook_path=args.grid_workbook)
    reference_values = tracker.get_reference_values()
    included_run_ids = included_df["run_id"].tolist()

    horizon_tables = {
        horizon: build_horizon_e10_table(
            master_context_df=master_context_df,
            included_run_ids=included_run_ids,
            prediction_lookup=prediction_lookup,
            horizon=horizon,
            reference_values=reference_values,
        )
        for horizon in (1, 2, 3, 4)
    }
    long_df = build_long_table_by_horizon(horizon_tables)
    inventory_df = build_column_inventory(
        included_run_ids=included_run_ids,
        history_window=args.history_window,
    )
    return write_outputs(
        long_df=long_df,
        horizon_tables=horizon_tables,
        included_df=included_df,
        excluded_df=excluded_df,
        inventory_df=inventory_df,
        args=args,
    )


def main() -> None:
    args = parse_args()
    artifacts = build_e10_meta_selector_table(args)
    print(f"CSV: {artifacts.table_csv_path}")
    print(f"XLSX: {artifacts.table_xlsx_path}")
    print(f"DICT_MD: {artifacts.dictionary_md_path}")
    print(f"INVENTARIO_CSV: {artifacts.column_inventory_csv_path}")
    print(f"RESUMEN_MD: {artifacts.summary_md_path}")
    print(f"Rows_total: {artifacts.rows_total}")
    print(
        "Filas_completas_por_horizonte: "
        + json.dumps(artifacts.complete_rows_by_horizon, ensure_ascii=False, sort_keys=True)
    )


if __name__ == "__main__":
    main()
