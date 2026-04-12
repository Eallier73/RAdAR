#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import DATE_COLUMN, ROOT_DIR
from evaluation import compute_loss_h, compute_radar_metrics, compute_total_radar_loss
from experiment_logger import DEFAULT_RUNS_DIR, DEFAULT_WORKBOOK, RadarExperimentTracker
from pipeline_common import normalize_reference_run_ids, parse_horizons, parse_string_sequence, save_reference_comparisons


DEFAULT_E10_TABLE_PATH = ROOT_DIR / "experiments" / "audit" / "tabla_e10_meta_selector_base.csv"
DEFAULT_E10_TABLE_SHEET = "E10_base_long"
DEFAULT_E10_INVENTORY_PATH = ROOT_DIR / "experiments" / "audit" / "inventario_columnas_e10.csv"
TARGET_EQUIVALENT_COLUMN = "mejor_modelo_operativo"
DEFAULT_TARGET_COLUMN = "mejor_modelo_loss_radar_local"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E10 | Meta-selector duro retrospectivo y comparable por horizonte.",
    )
    parser.add_argument("--run-id", default="E10_v1_clean")
    parser.add_argument("--reference-run-id", default="E1_v5_clean")
    parser.add_argument(
        "--extra-reference-run-ids",
        default="E9_v2_clean",
        help="Run_IDs extra para comparacion historica contra benchmarks centrales.",
    )
    parser.add_argument(
        "--hypothesis-note",
        default="meta_selector_duro_logistico_loss_local",
        help="Nota corta de hipotesis para comentarios y grid.",
    )
    parser.add_argument(
        "--table-path",
        type=Path,
        default=DEFAULT_E10_TABLE_PATH,
        help="Tabla operativa de E10 en CSV o XLSX.",
    )
    parser.add_argument(
        "--table-sheet-name",
        default=DEFAULT_E10_TABLE_SHEET,
        help="Hoja a usar cuando table-path sea XLSX.",
    )
    parser.add_argument(
        "--inventory-path",
        type=Path,
        default=DEFAULT_E10_INVENTORY_PATH,
        help="Inventario de columnas de la tabla E10.",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook principal del tracker.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Directorio donde se guardan runs y artefactos.",
    )
    parser.add_argument(
        "--horizons",
        default="1,2,3,4",
        help="Horizontes a correr separados por coma.",
    )
    parser.add_argument(
        "--initial-train-size",
        type=int,
        default=12,
        help="Tamano inicial de entrenamiento por horizonte sobre la tabla E10.",
    )
    parser.add_argument(
        "--target-column",
        default=DEFAULT_TARGET_COLUMN,
        help="Target retrospectivo canonico del selector.",
    )
    parser.add_argument(
        "--meta-model",
        choices=("logistic_regression",),
        default="logistic_regression",
    )
    parser.add_argument(
        "--selector-c",
        type=float,
        default=0.1,
        help="Inversa de regularizacion C para LogisticRegression.",
    )
    parser.add_argument(
        "--solver",
        choices=("lbfgs",),
        default="lbfgs",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=5000,
    )
    parser.add_argument(
        "--class-weight",
        choices=("balanced", "none"),
        default="balanced",
        help="Ponderacion de clases del selector.",
    )
    parser.add_argument(
        "--use-only-complete-rows",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Restringe E10 a filas completas; por defecto usa toda la tabla elegible.",
    )
    args = parser.parse_args()
    args.table_path = args.table_path.expanduser().resolve()
    args.inventory_path = args.inventory_path.expanduser().resolve()
    args.workbook = args.workbook.expanduser().resolve()
    args.runs_dir = args.runs_dir.expanduser().resolve()
    args.horizons = parse_horizons(args.horizons)
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def load_e10_table(table_path: Path, *, table_sheet_name: str) -> pd.DataFrame:
    suffix = table_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(table_path)
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        df = pd.read_excel(table_path, sheet_name=table_sheet_name)
    else:
        raise ValueError(f"Formato de tabla E10 no soportado: {table_path}")
    if DATE_COLUMN not in df.columns and "fecha" not in df.columns:
        raise ValueError(
            f"La tabla E10 no contiene ni `{DATE_COLUMN}` ni `fecha`; columnas disponibles: {sorted(df.columns)}"
        )
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])
    if DATE_COLUMN in df.columns:
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    elif "fecha" in df.columns:
        df[DATE_COLUMN] = df["fecha"]
    if "fecha" not in df.columns:
        df["fecha"] = df[DATE_COLUMN]
    return df


def load_inventory(inventory_path: Path) -> pd.DataFrame:
    inventory = pd.read_csv(inventory_path)
    required_columns = {
        "column_name",
        "block",
        "descripcion",
        "formula_o_fuente",
        "usa_y_real",
        "observable_en_t",
        "puede_ser_feature",
        "role",
        "riesgo_leakage",
        "comentario_metodologico",
    }
    missing = sorted(required_columns.difference(inventory.columns))
    if missing:
        raise ValueError(f"Inventario E10 incompleto. Faltan columnas: {missing}")
    return inventory


def get_role_columns(inventory: pd.DataFrame, role: str) -> list[str]:
    subset = inventory.loc[inventory["role"] == role, "column_name"]
    return [str(value) for value in subset.tolist()]


def get_feature_candidate_columns(inventory: pd.DataFrame) -> list[str]:
    subset = inventory.loc[
        (inventory["role"] == "feature_candidate") & (inventory["puede_ser_feature"].astype(bool)),
        "column_name",
    ]
    return [str(value) for value in subset.tolist()]


def infer_included_model_ids(feature_columns: list[str]) -> list[str]:
    model_ids = []
    for column in feature_columns:
        if column.startswith("pred_") and not column.startswith("pred_disponible_"):
            model_id = column.removeprefix("pred_")
            if model_id not in model_ids:
                model_ids.append(model_id)
    if not model_ids:
        raise ValueError("No se pudieron inferir modelos base desde las columnas pred_* de E10.")
    return model_ids


def build_selector_pipeline(*, selector_c: float, class_weight: str, solver: str, max_iter: int) -> Pipeline:
    resolved_class_weight = None if class_weight == "none" else class_weight
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=float(selector_c),
                    penalty="l2",
                    solver=solver,
                    multi_class="multinomial",
                    max_iter=int(max_iter),
                    class_weight=resolved_class_weight,
                    random_state=42,
                ),
            ),
        ]
    )


def filter_feature_columns_for_fold(
    *,
    train_df: pd.DataFrame,
    candidate_columns: list[str],
    horizon: int,
    outer_fold_index: int,
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[str] = []
    excluded_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []

    for column in candidate_columns:
        if column not in train_df.columns:
            excluded_rows.append(
                {
                    "horizonte_sem": int(horizon),
                    "outer_fold_index": int(outer_fold_index),
                    "column_name": column,
                    "reason": "missing_in_table",
                    "non_null_train_count": 0,
                    "nunique_train_non_null": 0,
                }
            )
            continue

        series = pd.to_numeric(train_df[column], errors="coerce")
        non_null = series.dropna()
        non_null_count = int(non_null.shape[0])
        unique_non_null = int(non_null.nunique(dropna=True))

        if non_null.empty:
            excluded_rows.append(
                {
                    "horizonte_sem": int(horizon),
                    "outer_fold_index": int(outer_fold_index),
                    "column_name": column,
                    "reason": "all_nan_in_train",
                    "non_null_train_count": non_null_count,
                    "nunique_train_non_null": unique_non_null,
                }
            )
            continue

        if unique_non_null <= 1:
            excluded_rows.append(
                {
                    "horizonte_sem": int(horizon),
                    "outer_fold_index": int(outer_fold_index),
                    "column_name": column,
                    "reason": "zero_variance_in_train",
                    "non_null_train_count": non_null_count,
                    "nunique_train_non_null": unique_non_null,
                }
            )
            continue

        selected.append(column)
        selected_rows.append(
            {
                "horizonte_sem": int(horizon),
                "outer_fold_index": int(outer_fold_index),
                "column_name": column,
                "non_null_train_count": non_null_count,
                "nunique_train_non_null": unique_non_null,
            }
        )

    return selected, selected_rows, excluded_rows


def get_available_models_for_row(row: pd.Series, model_ids: list[str]) -> list[str]:
    available = []
    for model_id in model_ids:
        pred_column = f"pred_{model_id}"
        available_column = f"pred_disponible_{model_id}"
        if pred_column not in row.index:
            continue
        if available_column in row.index and float(row[available_column] or 0.0) < 0.5:
            continue
        if pd.isna(row[pred_column]):
            continue
        available.append(model_id)
    return available


def build_fixed_model_ranking(train_df: pd.DataFrame, model_ids: list[str]) -> list[dict[str, Any]]:
    ranking_rows: list[dict[str, Any]] = []
    for model_id in model_ids:
        loss_column = f"loss_local_{model_id}"
        if loss_column not in train_df.columns:
            continue
        valid = pd.to_numeric(train_df[loss_column], errors="coerce").dropna()
        if valid.empty:
            continue
        ranking_rows.append(
            {
                "model_id": model_id,
                "mean_loss_local_train": float(valid.mean()),
                "std_loss_local_train": float(valid.std(ddof=0)),
                "rows_train_with_loss": int(valid.shape[0]),
            }
        )
    ranking_rows.sort(key=lambda item: (item["mean_loss_local_train"], item["model_id"]))
    for index, row in enumerate(ranking_rows, start=1):
        row["rank"] = index
    return ranking_rows


def choose_available_model_by_ranking(
    *,
    ranking_rows: list[dict[str, Any]],
    available_models: list[str],
) -> tuple[str, str]:
    if not available_models:
        return "", "no_available_models"

    ranked_ids = [row["model_id"] for row in ranking_rows]
    for model_id in ranked_ids:
        if model_id in available_models:
            return model_id, "ranking_best_available"

    fallback_model = sorted(available_models)[0]
    return fallback_model, "fallback_first_available"


def choose_selector_model_for_row(
    *,
    raw_prediction: str,
    probability_by_class: dict[str, float],
    available_models: list[str],
    ranking_rows: list[dict[str, Any]],
) -> tuple[str, str, float | None]:
    if raw_prediction and raw_prediction in available_models:
        return raw_prediction, "raw_prediction_available", probability_by_class.get(raw_prediction)

    if probability_by_class:
        ordered = sorted(probability_by_class.items(), key=lambda item: (-item[1], item[0]))
        for model_id, probability in ordered:
            if model_id in available_models:
                return model_id, "best_available_by_probability", float(probability)

    fallback_model, fallback_reason = choose_available_model_by_ranking(
        ranking_rows=ranking_rows,
        available_models=available_models,
    )
    probability = probability_by_class.get(fallback_model) if fallback_model else None
    return fallback_model, fallback_reason, probability


def compute_selector_metrics(
    *,
    actual: pd.Series,
    predicted: pd.Series,
    model_ids: list[str],
) -> dict[str, Any]:
    labels = [model_id for model_id in model_ids if model_id in set(actual) or model_id in set(predicted)]
    if not labels:
        labels = sorted(set(actual).union(set(predicted)))

    accuracy = float(accuracy_score(actual, predicted))
    if len(set(actual)) >= 2:
        balanced_accuracy = float(balanced_accuracy_score(actual, predicted))
    else:
        balanced_accuracy = None

    confusion = confusion_matrix(actual, predicted, labels=labels).tolist()
    return {
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "class_distribution_real": actual.value_counts().to_dict(),
        "class_distribution_pred": predicted.value_counts().to_dict(),
        "confusion_labels": labels,
        "confusion_matrix": confusion,
        "n_classes_real": int(actual.nunique()),
        "n_classes_pred": int(predicted.nunique()),
    }


def build_horizon_predictions_metrics(
    *,
    predictions_df: pd.DataFrame,
    prediction_column: str,
    horizon: int,
    reference_values: dict[str, Any],
) -> tuple[dict[str, Any] | None, pd.DataFrame]:
    subset = predictions_df.loc[predictions_df[prediction_column].notna()].copy()
    if subset.empty:
        return None, subset
    eval_df = subset[[DATE_COLUMN, "y_current", "y_true", prediction_column]].rename(columns={prediction_column: "y_pred"})
    metrics = compute_radar_metrics(eval_df)
    loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
    payload = {
        "rows_eval": int(eval_df.shape[0]),
        "loss_h": float(loss_h),
        "mae": float(metrics["mae"]),
        "rmse": float(metrics["rmse"]),
        "direccion_accuracy": float(metrics["direccion_accuracy"]),
        "deteccion_caidas": float(metrics["deteccion_caidas"]),
        "l_num": float(metrics["l_num"]),
        "l_trend": float(metrics["l_trend"]),
        "l_risk": float(metrics["l_risk"]),
        "l_tol": float(metrics["l_tol"]),
    }
    return payload, eval_df


def summarize_target_alignment(table_df: pd.DataFrame, target_column: str) -> dict[str, Any]:
    if target_column not in table_df.columns:
        raise ValueError(f"No existe el target solicitado en la tabla E10: {target_column}")
    if TARGET_EQUIVALENT_COLUMN not in table_df.columns:
        raise ValueError(f"No existe la columna de control {TARGET_EQUIVALENT_COLUMN} en la tabla E10.")

    valid = table_df[[target_column, TARGET_EQUIVALENT_COLUMN]].dropna()
    same_share = float((valid[target_column] == valid[TARGET_EQUIVALENT_COLUMN]).mean()) if not valid.empty else None
    mismatch_mask = table_df[target_column].notna() & table_df[TARGET_EQUIVALENT_COLUMN].notna() & (
        table_df[target_column] != table_df[TARGET_EQUIVALENT_COLUMN]
    )
    mismatch_columns = [column for column in (DATE_COLUMN, "fecha", "horizonte", target_column, TARGET_EQUIVALENT_COLUMN) if column in table_df.columns]
    mismatches = table_df.loc[mismatch_mask, mismatch_columns]
    per_horizon = {}
    for horizon, horizon_df in table_df.groupby("horizonte"):
        valid_h = horizon_df[[target_column, TARGET_EQUIVALENT_COLUMN]].dropna()
        same_share_h = float((valid_h[target_column] == valid_h[TARGET_EQUIVALENT_COLUMN]).mean()) if not valid_h.empty else None
        per_horizon[int(horizon)] = {
            "same_share": same_share_h,
            "target_distribution": horizon_df[target_column].value_counts(dropna=False).to_dict(),
            "operativo_distribution": horizon_df[TARGET_EQUIVALENT_COLUMN].value_counts(dropna=False).to_dict(),
        }
    return {
        "target_column": target_column,
        "equivalent_column": TARGET_EQUIVALENT_COLUMN,
        "same_share_global": same_share,
        "mismatch_count": int(mismatches.shape[0]),
        "mismatches_sample": mismatches.head(20).to_dict(orient="records"),
        "per_horizon": per_horizon,
    }


def build_run_parameters(
    args: argparse.Namespace,
    *,
    included_model_ids: list[str],
    feature_candidate_columns: list[str],
) -> dict[str, Any]:
    return {
        "table_path": str(args.table_path),
        "table_sheet_name": args.table_sheet_name,
        "inventory_path": str(args.inventory_path),
        "target_column": args.target_column,
        "horizons": list(args.horizons),
        "initial_train_size": args.initial_train_size,
        "meta_model": args.meta_model,
        "selector_c": args.selector_c,
        "solver": args.solver,
        "max_iter": args.max_iter,
        "class_weight": args.class_weight,
        "use_only_complete_rows": args.use_only_complete_rows,
        "included_model_ids": included_model_ids,
        "feature_candidate_columns": feature_candidate_columns,
    }


def build_summary_markdown(
    *,
    args: argparse.Namespace,
    target_alignment: dict[str, Any],
    horizon_summaries: list[dict[str, Any]],
    benchmark_payload: dict[str, Any],
    total_radar: dict[str, Any],
) -> str:
    lines = [
        "# Resumen ejecucion E10_v1_clean",
        "",
        f"- run_id: `{args.run_id}`",
        f"- tabla_e10: `{args.table_path}`",
        f"- inventario_columnas: `{args.inventory_path}`",
        f"- target_selector: `{args.target_column}`",
        f"- target_vs_operativo_same_share: `{target_alignment['same_share_global']}`",
        f"- initial_train_size: `{args.initial_train_size}`",
        f"- meta_model: `{args.meta_model}`",
        f"- selector_c: `{args.selector_c}`",
        f"- class_weight: `{args.class_weight}`",
        f"- use_only_complete_rows: `{args.use_only_complete_rows}`",
        f"- L_total_Radar_E10: `{total_radar['l_total_radar']:.6f}`",
        "",
        "## Horizontes",
        "",
    ]
    for summary in horizon_summaries:
        selector_metrics = summary["selector_metrics"]
        system_metrics = summary["system_metrics"]
        lines.extend(
            [
                f"### H{summary['horizonte_sem']}",
                "",
                f"- rows_total_horizonte: `{summary['rows_total_horizonte']}`",
                f"- rows_eval: `{summary['rows_eval']}`",
                f"- clases_train_iniciales: `{summary['target_distribution_train_initial']}`",
                f"- accuracy_selector: `{selector_metrics['accuracy']:.6f}`",
                f"- balanced_accuracy_selector: `{selector_metrics['balanced_accuracy']}`",
                f"- loss_h_E10: `{system_metrics['loss_h']:.6f}`",
                f"- benchmark_fijo_loss_h: `{summary['benchmark_fixed_metrics']['loss_h']:.6f}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Lectura corta",
            "",
            "- E10 se evalua como selector duro retrospectivo, pero el criterio principal sigue siendo el sistema final Radar.",
            "- El benchmark fijo se construye dentro de train con perdida local historica media y nunca usa el bloque de test para definirse.",
            "- Las columnas prohibidas, diagnosticas y targets retrospectivos no entran al entrenamiento del selector.",
            "",
            "## Benchmarks globales sobre el mismo subset de evaluacion",
            "",
            f"- selector_fijo: `{benchmark_payload['global']['selector_fijo']['l_total_radar']:.6f}`",
            f"- E1_v5_clean: `{benchmark_payload['global']['E1_v5_clean']['l_total_radar']}`",
            f"- E9_v2_clean: `{benchmark_payload['global']['E9_v2_clean']['l_total_radar']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def run_horizon(
    *,
    args: argparse.Namespace,
    run,
    table_df: pd.DataFrame,
    feature_candidate_columns: list[str],
    included_model_ids: list[str],
    target_alignment: dict[str, Any],
    reference_values: dict[str, Any],
    horizon: int,
) -> dict[str, Any]:
    horizon_df = table_df.loc[table_df["horizonte"] == int(horizon)].copy()
    if args.use_only_complete_rows:
        horizon_df = horizon_df.loc[horizon_df["fila_completa_modelos_incluidos"].astype(bool)].copy()
    horizon_df = horizon_df.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)

    if horizon_df.shape[0] <= args.initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para E10 en H{horizon}. "
            f"Filas={horizon_df.shape[0]}, initial_train_size={args.initial_train_size}."
        )

    prediction_rows: list[dict[str, Any]] = []
    selector_trace: list[dict[str, Any]] = []
    selected_columns_rows: list[dict[str, Any]] = []
    excluded_columns_rows: list[dict[str, Any]] = []

    initial_target_distribution = horizon_df.iloc[: args.initial_train_size][args.target_column].value_counts().to_dict()

    for test_idx in range(args.initial_train_size, horizon_df.shape[0]):
        outer_fold_index = test_idx - args.initial_train_size + 1
        train_df = horizon_df.iloc[:test_idx].copy()
        test_row = horizon_df.iloc[test_idx].copy()

        usable_columns, selected_rows, excluded_rows = filter_feature_columns_for_fold(
            train_df=train_df,
            candidate_columns=feature_candidate_columns,
            horizon=horizon,
            outer_fold_index=outer_fold_index,
        )
        selected_columns_rows.extend(selected_rows)
        excluded_columns_rows.extend(excluded_rows)

        y_train = train_df[args.target_column].astype(str)
        train_classes = sorted(y_train.unique().tolist())
        train_class_distribution = y_train.value_counts().to_dict()
        available_models_test = get_available_models_for_row(test_row, included_model_ids)
        ranking_rows = build_fixed_model_ranking(train_df, included_model_ids)
        fixed_model_raw = ranking_rows[0]["model_id"] if ranking_rows else ""
        fixed_model_selected, fixed_selection_reason = choose_available_model_by_ranking(
            ranking_rows=ranking_rows,
            available_models=available_models_test,
        )

        probability_by_class: dict[str, float] = {}
        raw_selector_prediction = ""
        selector_mode = ""
        coefficient_map: dict[str, float] | None = None
        intercept_value: float | None = None

        if not usable_columns:
            selector_mode = "fallback_no_features_majority_class"
            raw_selector_prediction = str(y_train.value_counts().idxmax())
            probability_by_class = {raw_selector_prediction: 1.0}
        elif len(train_classes) < 2:
            selector_mode = "constant_single_class_train"
            raw_selector_prediction = train_classes[0]
            probability_by_class = {raw_selector_prediction: 1.0}
        else:
            selector_mode = "logistic_regression_multinomial"
            selector_pipeline = build_selector_pipeline(
                selector_c=args.selector_c,
                class_weight=args.class_weight,
                solver=args.solver,
                max_iter=args.max_iter,
            )
            selector_pipeline.fit(train_df[usable_columns], y_train)
            raw_selector_prediction = str(selector_pipeline.predict(horizon_df.iloc[[test_idx]][usable_columns])[0])
            probabilities = selector_pipeline.predict_proba(horizon_df.iloc[[test_idx]][usable_columns])[0]
            trained_classes = selector_pipeline.named_steps["model"].classes_.tolist()
            probability_by_class = {
                str(model_id): float(probability)
                for model_id, probability in zip(trained_classes, probabilities, strict=True)
            }
            model = selector_pipeline.named_steps["model"]
            coef = np.asarray(model.coef_, dtype=float)
            if coef.ndim == 2 and coef.shape[0] >= 1:
                if coef.shape[0] == 1:
                    coef_vector = coef.reshape(-1)
                else:
                    coef_vector = np.mean(np.abs(coef), axis=0)
                coefficient_map = {
                    column: float(value) for column, value in zip(usable_columns, coef_vector, strict=True)
                }
            intercept = np.asarray(model.intercept_, dtype=float)
            if intercept.shape == ():
                intercept_value = float(intercept)
            elif intercept.size:
                intercept_value = float(np.mean(intercept))

        selected_model, selected_reason, selected_probability = choose_selector_model_for_row(
            raw_prediction=raw_selector_prediction,
            probability_by_class=probability_by_class,
            available_models=available_models_test,
            ranking_rows=ranking_rows,
        )
        if not selected_model:
            raise ValueError(
                f"No se pudo seleccionar modelo disponible en H{horizon}, fold {outer_fold_index}, fecha {test_row[DATE_COLUMN]}."
            )

        true_best_model = str(test_row[args.target_column])
        y_pred_final = float(test_row[f"pred_{selected_model}"])
        fixed_prediction = float(test_row[f"pred_{fixed_model_selected}"]) if fixed_model_selected else np.nan
        true_best_prediction = float(test_row[f"pred_{true_best_model}"]) if f"pred_{true_best_model}" in test_row.index else np.nan

        prediction_row: dict[str, Any] = {
            DATE_COLUMN: pd.to_datetime(test_row[DATE_COLUMN]),
            "fecha": pd.to_datetime(test_row[DATE_COLUMN]),
            "horizonte": int(horizon),
            "outer_fold_index": int(outer_fold_index),
            "y_current": float(test_row["y_current"]),
            "y_true": float(test_row["y_real"]),
            "modelo_ganador_real": true_best_model,
            "modelo_ganador_real_operativo": str(test_row[TARGET_EQUIVALENT_COLUMN]),
            "modelo_predicho_raw": raw_selector_prediction,
            "modelo_predicho": selected_model,
            "modelo_selector_fijo_raw": fixed_model_raw,
            "modelo_selector_fijo": fixed_model_selected,
            "prediccion_modelo_elegido": y_pred_final,
            "prediccion_modelo_ganador_real": true_best_prediction,
            "prediccion_selector_fijo": fixed_prediction,
            "error_final": float(y_pred_final - float(test_row["y_real"])),
            "indicador_acierto_selector": int(selected_model == true_best_model),
            "indicador_acierto_selector_fijo": int(fixed_model_selected == true_best_model),
            "prob_modelo_predicho": float(selected_probability) if selected_probability is not None else np.nan,
            "probabilidades_clases_json": json.dumps(probability_by_class, ensure_ascii=False, sort_keys=True),
            "selection_mode": selector_mode,
            "selection_reason": selected_reason,
            "fixed_selection_reason": fixed_selection_reason,
            "rows_train": int(train_df.shape[0]),
            "n_clases_train": int(len(train_classes)),
            "clases_train": ",".join(train_classes),
            "n_modelos_disponibles_test": int(len(available_models_test)),
            "modelos_disponibles_test": ",".join(available_models_test),
        }
        for model_id in included_model_ids:
            prediction_row[f"prediccion_{model_id}"] = (
                float(test_row[f"pred_{model_id}"]) if f"pred_{model_id}" in test_row.index and pd.notna(test_row[f"pred_{model_id}"]) else np.nan
            )
        prediction_rows.append(prediction_row)

        selector_trace.append(
            {
                "horizonte_sem": int(horizon),
                "outer_fold_index": int(outer_fold_index),
                "fecha_test": pd.to_datetime(test_row[DATE_COLUMN]).strftime("%Y-%m-%d"),
                "rows_train": int(train_df.shape[0]),
                "rows_test": 1,
                "target_column": args.target_column,
                "target_operativo_same_share_horizon": target_alignment["per_horizon"][int(horizon)]["same_share"],
                "clases_train": train_classes,
                "class_distribution_train": train_class_distribution,
                "clase_real_test": true_best_model,
                "clase_real_operativa_test": str(test_row[TARGET_EQUIVALENT_COLUMN]),
                "selector_mode": selector_mode,
                "feature_count_used": int(len(usable_columns)),
                "feature_columns_used": usable_columns,
                "excluded_columns_count": int(len(excluded_rows)),
                "excluded_columns_reasons": excluded_rows,
                "modelo_predicho_raw": raw_selector_prediction,
                "modelo_predicho_final": selected_model,
                "selection_reason": selected_reason,
                "available_models_test": available_models_test,
                "probability_by_class": probability_by_class,
                "ranking_fixed_train": ranking_rows,
                "fixed_model_selected": fixed_model_selected,
                "fixed_selection_reason": fixed_selection_reason,
                "coeficientes_resumen": coefficient_map if coefficient_map is not None else {},
                "intercept_resumen": intercept_value,
            }
        )

    predictions_df = pd.DataFrame(prediction_rows).sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)
    selector_metrics = compute_selector_metrics(
        actual=predictions_df["modelo_ganador_real"].astype(str),
        predicted=predictions_df["modelo_predicho"].astype(str),
        model_ids=included_model_ids,
    )
    system_metrics, _ = build_horizon_predictions_metrics(
        predictions_df=predictions_df,
        prediction_column="prediccion_modelo_elegido",
        horizon=horizon,
        reference_values=reference_values,
    )
    if system_metrics is None:
        raise ValueError(f"No se pudieron calcular metricas del sistema final para H{horizon}.")

    benchmark_fixed_metrics, _ = build_horizon_predictions_metrics(
        predictions_df=predictions_df,
        prediction_column="prediccion_selector_fijo",
        horizon=horizon,
        reference_values=reference_values,
    )
    benchmark_e1_metrics, _ = build_horizon_predictions_metrics(
        predictions_df=predictions_df,
        prediction_column="prediccion_E1_v5_clean",
        horizon=horizon,
        reference_values=reference_values,
    )
    benchmark_e9_metrics, _ = build_horizon_predictions_metrics(
        predictions_df=predictions_df,
        prediction_column="prediccion_E9_v2_clean",
        horizon=horizon,
        reference_values=reference_values,
    )

    confusion_payload = {
        "horizonte_sem": int(horizon),
        **selector_metrics,
    }

    run.save_dataframe(
        predictions_df,
        f"predicciones_h{horizon}.csv",
        artifact_type="predicciones",
        notes="Predicciones finales del selector, benchmarks y predicciones base por fila de test.",
    )
    run.save_dataframe(
        pd.DataFrame(selected_columns_rows),
        f"columnas_entrenamiento_h{horizon}.csv",
        artifact_type="columnas",
        notes="Columnas permitidas efectivamente usadas por fold en el selector E10.",
    )
    run.save_dataframe(
        pd.DataFrame(excluded_columns_rows),
        f"columnas_excluidas_h{horizon}.csv",
        artifact_type="columnas_excluidas",
        notes="Columnas excluidas por fold y motivo exacto de exclusion.",
    )
    run.save_json(
        confusion_payload,
        f"matriz_confusion_h{horizon}.json",
        artifact_type="confusion",
        notes="Matriz de confusion y distribucion de clases del selector por horizonte.",
    )
    run.save_json(
        {
            "horizonte_sem": int(horizon),
            "target_column": args.target_column,
            "target_operativo_same_share_horizon": target_alignment["per_horizon"][int(horizon)]["same_share"],
            "rows_total_horizonte": int(horizon_df.shape[0]),
            "rows_eval": int(predictions_df.shape[0]),
            "initial_train_size": int(args.initial_train_size),
            "target_distribution_train_initial": initial_target_distribution,
            "selector_metrics": selector_metrics,
            "system_metrics": system_metrics,
            "benchmark_fixed_metrics": benchmark_fixed_metrics,
            "benchmark_e1_metrics": benchmark_e1_metrics,
            "benchmark_e9_metrics": benchmark_e9_metrics,
        },
        f"metricas_h{horizon}.json",
        artifact_type="metricas_horizonte_detalle",
        notes="Metricas completas del selector y del sistema final para este horizonte.",
    )
    run.save_json(
        {
            "horizonte_sem": int(horizon),
            "target_column": args.target_column,
            "folds": selector_trace,
        },
        f"selector_trace_h{horizon}.json",
        artifact_type="trace_selector",
        notes="Traza detallada por fold del meta-selector E10.",
    )

    horizon_result = {
        "horizonte_sem": int(horizon),
        "target": "nivel",
        "variables_temporales": "predicciones_base_contexto_disagreement_e10",
        "variables_tematicas": ", ".join(included_model_ids),
        "transformacion": "imputer_median_plus_scaler_in_pipeline",
        "seleccion_variables": "solo_feature_candidate_desde_inventario_e10",
        "validacion": "walk-forward_expanding_meta_selector_duro",
        "dataset_periodo": f"{predictions_df[DATE_COLUMN].min().date()} a {predictions_df[DATE_COLUMN].max().date()}",
        "notas_config": json.dumps(
            {
                "target_column": args.target_column,
                "rows_total_horizonte": int(horizon_df.shape[0]),
                "rows_eval": int(predictions_df.shape[0]),
                "initial_train_size": int(args.initial_train_size),
                "feature_candidates_total": int(len(feature_candidate_columns)),
                "feature_columns_used_union": sorted({row["column_name"] for row in selected_columns_rows}),
                "meta_model": args.meta_model,
                "selector_c": args.selector_c,
                "class_weight": args.class_weight,
                "solver": args.solver,
                "max_iter": args.max_iter,
                "use_only_complete_rows": args.use_only_complete_rows,
                "target_vs_operativo_same_share_horizon": target_alignment["per_horizon"][int(horizon)]["same_share"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        "estado": "corrido",
        "comentarios": args.hypothesis_note,
        **system_metrics,
    }

    rows_summary = {
        "horizonte_sem": int(horizon),
        "rows_total_horizonte": int(horizon_df.shape[0]),
        "rows_eval": int(predictions_df.shape[0]),
        "initial_train_size": int(args.initial_train_size),
        "rows_complete_available": int(horizon_df["fila_completa_modelos_incluidos"].astype(bool).sum()),
        "target_distribution_train_initial": initial_target_distribution,
        "feature_candidates_total": int(len(feature_candidate_columns)),
        "feature_columns_used_union_count": int(len({row["column_name"] for row in selected_columns_rows})),
        "feature_columns_used_union": sorted({row["column_name"] for row in selected_columns_rows}),
        "excluded_columns_count": int(len(excluded_columns_rows)),
        "selector_accuracy": float(selector_metrics["accuracy"]),
        "selector_balanced_accuracy": selector_metrics["balanced_accuracy"],
        "benchmark_fixed_loss_h": benchmark_fixed_metrics["loss_h"] if benchmark_fixed_metrics else None,
    }

    return {
        "predictions": predictions_df,
        "selector_trace": selector_trace,
        "selected_columns_rows": selected_columns_rows,
        "excluded_columns_rows": excluded_columns_rows,
        "selector_metrics": selector_metrics,
        "system_metrics": system_metrics,
        "benchmark_fixed_metrics": benchmark_fixed_metrics,
        "benchmark_e1_metrics": benchmark_e1_metrics,
        "benchmark_e9_metrics": benchmark_e9_metrics,
        "horizon_result": horizon_result,
        "rows_summary": rows_summary,
    }


def aggregate_benchmark_results(
    *,
    per_horizon_payloads: list[dict[str, Any]],
    reference_values: dict[str, Any],
) -> dict[str, Any]:
    valid_rows = [
        {
            "horizonte_sem": item["horizonte_sem"],
            "mae": item["mae"],
            "rmse": item["rmse"],
            "direccion_accuracy": item["direccion_accuracy"],
            "deteccion_caidas": item["deteccion_caidas"],
            "l_num": item["l_num"],
            "l_trend": item["l_trend"],
            "l_risk": item["l_risk"],
            "l_tol": item["l_tol"],
            "loss_h": item["loss_h"],
        }
        for item in per_horizon_payloads
        if item is not None
    ]
    if not valid_rows:
        return {
            "l_total_radar": None,
            "avg_mae": None,
            "avg_rmse": None,
            "avg_direction_accuracy": None,
            "avg_deteccion_caidas": None,
            "horizontes": [],
        }
    totals = compute_total_radar_loss(horizon_results=valid_rows, reference_values=reference_values, l_coh=None)
    return {
        "l_total_radar": float(totals["l_total_radar"]),
        "avg_mae": float(np.mean([row["mae"] for row in valid_rows])),
        "avg_rmse": float(np.mean([row["rmse"] for row in valid_rows])),
        "avg_direction_accuracy": float(np.mean([row["direccion_accuracy"] for row in valid_rows])),
        "avg_deteccion_caidas": float(np.mean([row["deteccion_caidas"] for row in valid_rows])),
        "horizontes": [int(row["horizonte_sem"]) for row in valid_rows],
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)

    table_df = load_e10_table(args.table_path, table_sheet_name=args.table_sheet_name)
    inventory = load_inventory(args.inventory_path)
    feature_candidate_columns = [
        column for column in get_feature_candidate_columns(inventory) if column in table_df.columns
    ]
    included_model_ids = infer_included_model_ids(feature_candidate_columns)

    forbidden_columns = set(get_role_columns(inventory, "forbidden_for_training"))
    target_columns = set(get_role_columns(inventory, "target_selector"))
    diagnostic_columns = set(get_role_columns(inventory, "diagnostic_only"))
    id_columns = set(get_role_columns(inventory, "id"))
    overlap = set(feature_candidate_columns) & (forbidden_columns | target_columns | diagnostic_columns | id_columns)
    if overlap:
        raise ValueError(f"Inventario inconsistente: columnas feature_candidate tambien marcadas como no entrenables: {sorted(overlap)}")

    target_alignment = summarize_target_alignment(table_df, args.target_column)
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E10",
        family="gating_contextual",
        model="meta_selector_hard_logistic_regression",
        script_path=__file__,
        parametros=build_run_parameters(
            args,
            included_model_ids=included_model_ids,
            feature_candidate_columns=feature_candidate_columns,
        ),
    )

    horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    benchmark_fixed_rows: list[dict[str, Any] | None] = []
    benchmark_e1_rows: list[dict[str, Any] | None] = []
    benchmark_e9_rows: list[dict[str, Any] | None] = []
    benchmark_horizon_rows: list[dict[str, Any]] = []

    for horizon in args.horizons:
        horizon_output = run_horizon(
            args=args,
            run=run,
            table_df=table_df,
            feature_candidate_columns=feature_candidate_columns,
            included_model_ids=included_model_ids,
            target_alignment=target_alignment,
            reference_values=reference_values,
            horizon=horizon,
        )
        horizon_results.append(horizon_output["horizon_result"])
        rows_summary.append(horizon_output["rows_summary"])
        benchmark_fixed_rows.append(
            {"horizonte_sem": int(horizon), **(horizon_output["benchmark_fixed_metrics"] or {})}
            if horizon_output["benchmark_fixed_metrics"] is not None
            else None
        )
        benchmark_e1_rows.append(
            {"horizonte_sem": int(horizon), **(horizon_output["benchmark_e1_metrics"] or {})}
            if horizon_output["benchmark_e1_metrics"] is not None
            else None
        )
        benchmark_e9_rows.append(
            {"horizonte_sem": int(horizon), **(horizon_output["benchmark_e9_metrics"] or {})}
            if horizon_output["benchmark_e9_metrics"] is not None
            else None
        )
        benchmark_horizon_rows.append(
            {
                "horizonte_sem": int(horizon),
                "E10_v1_clean": horizon_output["system_metrics"],
                "selector_fijo": horizon_output["benchmark_fixed_metrics"],
                "E1_v5_clean": horizon_output["benchmark_e1_metrics"],
                "E9_v2_clean": horizon_output["benchmark_e9_metrics"],
                "selector_accuracy": horizon_output["selector_metrics"]["accuracy"],
                "selector_balanced_accuracy": horizon_output["selector_metrics"]["balanced_accuracy"],
            }
        )

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen por horizonte de tamanos muestrales, clases y columnas usadas.",
    )
    run.save_json(
        target_alignment,
        "target_selector_diagnostico.json",
        artifact_type="target_selector",
        notes="Diagnostico del target del selector y comparacion contra mejor_modelo_operativo.",
    )

    benchmark_payload = {
        "run_id": args.run_id,
        "target_column": args.target_column,
        "target_operativo_same_share_global": target_alignment["same_share_global"],
        "benchmark_strategy_fixed": "modelo_con_menor_mean_loss_local_train_por_fold_con_fallback_a_mejor_disponible",
        "per_horizon": benchmark_horizon_rows,
        "global": {
            "selector_fijo": aggregate_benchmark_results(per_horizon_payloads=benchmark_fixed_rows, reference_values=reference_values),
            "E1_v5_clean": aggregate_benchmark_results(per_horizon_payloads=benchmark_e1_rows, reference_values=reference_values),
            "E9_v2_clean": aggregate_benchmark_results(per_horizon_payloads=benchmark_e9_rows, reference_values=reference_values),
        },
    }
    run.save_json(
        benchmark_payload,
        "comparacion_vs_benchmarks.json",
        artifact_type="comparacion",
        notes="Comparacion de E10 contra selector fijo, E1_v5_clean y E9_v2_clean sobre el mismo subset de evaluacion.",
    )

    total_radar = compute_total_radar_loss(horizon_results=horizon_results, reference_values=reference_values, l_coh=None)

    run.save_text(
        build_summary_markdown(
            args=args,
            target_alignment=target_alignment,
            horizon_summaries=rows_summary,
            benchmark_payload=benchmark_payload,
            total_radar=total_radar,
        ),
        "resumen_ejecucion.md",
        artifact_type="resumen_ejecucion",
        notes="Resumen metodologico breve de la primera corrida canonica de E10.",
    )

    if reference_run_ids:
        save_reference_comparisons(
            run=run,
            workbook_path=tracker.workbook_path,
            clean_run_id=args.run_id,
            reference_run_ids=reference_run_ids,
            horizon_results=horizon_results,
            l_total_radar=float(total_radar["l_total_radar"]),
        )

    notas_config_payload = {
        "table_path": str(args.table_path),
        "inventory_path": str(args.inventory_path),
        "target_column": args.target_column,
        "target_vs_operativo_same_share_global": target_alignment["same_share_global"],
        "initial_train_size": args.initial_train_size,
        "meta_model": args.meta_model,
        "selector_c": args.selector_c,
        "class_weight": args.class_weight,
        "solver": args.solver,
        "max_iter": args.max_iter,
        "use_only_complete_rows": args.use_only_complete_rows,
        "included_model_ids": included_model_ids,
        "feature_candidate_count": len(feature_candidate_columns),
        "benchmark_strategy_fixed": benchmark_payload["benchmark_strategy_fixed"],
    }

    run.finalize(
        horizon_results=horizon_results,
        target="selector_duro_sobre_mejor_modelo_loss_radar_local",
        variables_temporales="predicciones_base_desacuerdo_contexto_observable_e10",
        variables_tematicas=", ".join(included_model_ids),
        transformacion="simple_imputer_median_plus_standard_scaler",
        seleccion_variables="inventario_e10_feature_candidate_con_filtros_por_fold",
        validacion="walk-forward_expanding_meta_selector_duro",
        dataset_periodo=f"{table_df[DATE_COLUMN].min().date()} a {table_df[DATE_COLUMN].max().date()}",
        notas_config=json.dumps(notas_config_payload, ensure_ascii=False, sort_keys=True),
        estado="corrido",
        comentarios=(
            f"{args.hypothesis_note} | target={args.target_column} | "
            f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        summary_metrics=total_radar,
    )

    print(f"Run registrado: {args.run_id}")
    print(f"L_total_Radar: {total_radar['l_total_radar']:.6f}")
    print(f"Target selector: {args.target_column}")


if __name__ == "__main__":
    main()
