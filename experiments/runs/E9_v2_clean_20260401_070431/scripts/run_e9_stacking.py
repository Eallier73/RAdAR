#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import (
    CURRENT_TARGET_COLUMN,
    DATASET_PATH,
    DATE_COLUMN,
    DEFAULT_HORIZONS,
    DEFAULT_SHEET_NAME,
    ROOT_DIR,
    TARGET_COLUMNS,
    TARGET_MODE_LEVEL,
)
from data_master import load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    select_best_alpha_time_series,
)
from experiment_logger import DEFAULT_RUNS_DIR, DEFAULT_WORKBOOK, RadarExperimentTracker
from pipeline_common import normalize_reference_run_ids, parse_horizons, parse_string_sequence, save_reference_comparisons


CURATED_E9_TABLE_PATH = ROOT_DIR / "experiments" / "audit" / "tabla_maestra_experimentos_radar_e9_curada.xlsx"
CURATED_BASE_SHEET_PREFIX = "E9_base_h"
NON_FEATURE_COLUMNS = {
    "fecha",
    "y_true",
    "n_modelos_disponibles",
    "fila_completa",
    "cobertura_modelos_fila",
}
E9_CANDIDATES_BY_HORIZON: dict[int, tuple[str, ...]] = {
    1: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
    2: ("E1_v5_clean", "E5_v4_clean", "E2_v3_clean", "E7_v3_clean"),
    3: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E7_v3_clean"),
    4: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E9 | Stacking clasico controlado por horizonte sobre tabla curada.",
    )
    parser.add_argument("--run-id", default="E9_v1_clean")
    parser.add_argument("--reference-run-id", default="E1_v5_clean")
    parser.add_argument(
        "--extra-reference-run-ids",
        default="E5_v4_clean,E3_v2_clean,E2_v3_clean,E7_v3_clean",
        help="Run_IDs extra para comparacion contra referencias historicas.",
    )
    parser.add_argument(
        "--hypothesis-note",
        default="stacking_clasico_controlado_ridge",
        help="Nota corta de la hipotesis del run.",
    )
    parser.add_argument(
        "--table-path",
        type=Path,
        default=CURATED_E9_TABLE_PATH,
        help="Workbook curado de E9 con las bases por horizonte.",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DATASET_PATH,
        help="Dataset maestro usado solo para reconstruir y_current y validar y_true.",
    )
    parser.add_argument(
        "--sheet-name",
        default=DEFAULT_SHEET_NAME,
        help="Hoja del dataset maestro.",
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
        help="Directorio de salida de runs.",
    )
    parser.add_argument(
        "--horizons",
        default=",".join(str(horizon) for horizon in DEFAULT_HORIZONS),
    )
    parser.add_argument(
        "--initial-train-size",
        type=int,
        default=12,
        help=(
            "Tamano inicial del entrenamiento sobre la tabla curada. "
            "Debe ser menor al numero de filas completas por horizonte."
        ),
    )
    parser.add_argument(
        "--meta-model",
        choices=("ridge", "huber"),
        default="ridge",
    )
    parser.add_argument(
        "--alpha-grid-size",
        type=int,
        default=40,
    )
    parser.add_argument(
        "--alpha-grid-min-exp",
        type=float,
        default=-4.0,
    )
    parser.add_argument(
        "--alpha-grid-max-exp",
        type=float,
        default=4.0,
    )
    parser.add_argument(
        "--inner-splits",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--alpha-selection-metric",
        choices=("mae", "rmse"),
        default="mae",
    )
    parser.add_argument(
        "--use-only-complete-rows",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Usar solo filas completas del workbook curado.",
    )
    args = parser.parse_args()
    args.table_path = args.table_path.expanduser().resolve()
    args.dataset_path = args.dataset_path.expanduser().resolve()
    args.workbook = args.workbook.expanduser().resolve()
    args.runs_dir = args.runs_dir.expanduser().resolve()
    args.horizons = parse_horizons(args.horizons)
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_ridge_estimator(alpha: float) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=float(alpha))),
        ]
    )


def build_huber_estimator() -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", HuberRegressor()),
        ]
    )


def extract_feature_columns(sheet_df: pd.DataFrame, horizon: int) -> list[str]:
    expected = list(E9_CANDIDATES_BY_HORIZON[int(horizon)])
    missing = [column for column in expected if column not in sheet_df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas de candidatos aprobados en {CURATED_BASE_SHEET_PREFIX}{horizon}: {missing}"
        )
    extra_model_columns = [
        column for column in sheet_df.columns if column not in NON_FEATURE_COLUMNS and column not in expected
    ]
    if extra_model_columns:
        raise ValueError(
            f"La hoja {CURATED_BASE_SHEET_PREFIX}{horizon} contiene columnas extra no aprobadas: {extra_model_columns}"
        )
    return expected


def load_curated_horizon_frame(
    *,
    table_path: Path,
    master_df: pd.DataFrame,
    horizon: int,
    use_only_complete_rows: bool,
) -> tuple[pd.DataFrame, list[str]]:
    sheet_name = f"{CURATED_BASE_SHEET_PREFIX}{horizon}"
    sheet_df = pd.read_excel(table_path, sheet_name=sheet_name)
    required_columns = {"fecha", "y_true", "fila_completa", "n_modelos_disponibles", "cobertura_modelos_fila"}
    missing_required = sorted(required_columns.difference(sheet_df.columns))
    if missing_required:
        raise ValueError(f"Faltan columnas requeridas en {sheet_name}: {missing_required}")

    feature_columns = extract_feature_columns(sheet_df, horizon=horizon)

    working_df = sheet_df.copy()
    working_df["fecha"] = pd.to_datetime(working_df["fecha"])
    if use_only_complete_rows:
        working_df = working_df.loc[working_df["fila_completa"].astype(bool)].copy()

    merge_columns = [DATE_COLUMN, CURRENT_TARGET_COLUMN, TARGET_COLUMNS[horizon]]
    merged = working_df.merge(
        master_df[merge_columns],
        left_on="fecha",
        right_on=DATE_COLUMN,
        how="left",
        validate="one_to_one",
    )
    if merged[CURRENT_TARGET_COLUMN].isna().any():
        missing_dates = merged.loc[merged[CURRENT_TARGET_COLUMN].isna(), "fecha"].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"No se pudo reconstruir y_current para {sheet_name}. Fechas faltantes: {missing_dates}")

    max_target_diff = float((merged["y_true"] - merged[TARGET_COLUMNS[horizon]]).abs().max())
    if max_target_diff > 1e-9:
        raise ValueError(
            f"Inconsistencia tecnica en {sheet_name}: y_true no coincide con {TARGET_COLUMNS[horizon]} "
            f"(max_diff={max_target_diff})."
        )

    merged["y_current"] = merged[CURRENT_TARGET_COLUMN].astype(float)
    merged["y_true"] = merged["y_true"].astype(float)
    for column in feature_columns:
        merged[column] = merged[column].astype(float)

    merged = merged.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)
    return merged, feature_columns


def build_prediction_record(
    *,
    test_row: pd.Series,
    feature_columns: list[str],
    horizon: int,
    run_id: str,
    meta_model: str,
    y_pred: float,
    alpha: float | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        DATE_COLUMN: pd.to_datetime(test_row[DATE_COLUMN]),
        "fecha": pd.to_datetime(test_row[DATE_COLUMN]),
        "y_current": float(test_row["y_current"]),
        "y_true": float(test_row["y_true"]),
        "y_pred": float(y_pred),
        "error": float(y_pred - float(test_row["y_true"])),
        "horizonte_sem": int(horizon),
        "run_id": run_id,
        "meta_model": meta_model,
        "n_modelos_base": len(feature_columns),
    }
    if alpha is not None:
        record["best_alpha"] = float(alpha)
    for column in feature_columns:
        record[column] = float(test_row[column])
    return record


def build_fold_trace(
    *,
    test_row: pd.Series,
    outer_fold_index: int,
    feature_columns: list[str],
    alpha_payload: dict[str, Any] | None,
    fitted_estimator: Pipeline,
) -> dict[str, Any]:
    trace: dict[str, Any] = {
        "outer_fold_index": int(outer_fold_index),
        "fecha_test": pd.to_datetime(test_row[DATE_COLUMN]).strftime("%Y-%m-%d"),
        "feature_columns": feature_columns,
    }
    if alpha_payload is not None:
        trace.update(
            {
                "best_alpha": float(alpha_payload["best_alpha"]),
                "best_score": float(alpha_payload["best_score"]),
                "tuning_metric": str(alpha_payload["tuning_metric"]),
                "inner_split_count": int(alpha_payload["inner_split_count"]),
                "alpha_results": alpha_payload["alpha_results"],
            }
        )

    if hasattr(fitted_estimator, "named_steps") and "model" in fitted_estimator.named_steps:
        model = fitted_estimator.named_steps["model"]
        coefficients = getattr(model, "coef_", None)
        intercept = getattr(model, "intercept_", None)
        if coefficients is not None:
            coef_vector = np.asarray(coefficients, dtype=float).reshape(-1)
            trace["coeficientes"] = {
                feature: float(coef) for feature, coef in zip(feature_columns, coef_vector, strict=True)
            }
        if intercept is not None:
            if np.asarray(intercept).shape == ():
                trace["intercept"] = float(intercept)
    return trace


def build_base_metrics_on_eval_subset(
    *,
    predictions_df: pd.DataFrame,
    feature_columns: list[str],
    horizon: int,
    reference_values: dict[str, Any],
) -> dict[str, Any]:
    base_rows: list[dict[str, Any]] = []
    best_base_run_id: str | None = None
    best_base_loss = float("inf")

    for run_id in feature_columns:
        base_predictions = predictions_df[[DATE_COLUMN, "y_current", "y_true", run_id]].rename(
            columns={run_id: "y_pred"}
        )
        metrics = compute_radar_metrics(base_predictions)
        loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
        row = {
            "run_id": run_id,
            "loss_h": float(loss_h),
            "mae": float(metrics["mae"]),
            "rmse": float(metrics["rmse"]),
            "direccion_accuracy": float(metrics["direccion_accuracy"]),
            "deteccion_caidas": float(metrics["deteccion_caidas"]),
        }
        base_rows.append(row)
        if row["loss_h"] < best_base_loss:
            best_base_loss = row["loss_h"]
            best_base_run_id = run_id

    return {
        "horizonte_sem": int(horizon),
        "rows_eval": int(len(predictions_df)),
        "base_models": base_rows,
        "best_base_run_id": best_base_run_id,
        "best_base_loss_h": float(best_base_loss),
    }


def run_stacking_for_horizon(
    *,
    args: argparse.Namespace,
    run,
    master_df: pd.DataFrame,
    reference_values: dict[str, Any],
    horizon: int,
) -> dict[str, Any]:
    horizon_df, feature_columns = load_curated_horizon_frame(
        table_path=args.table_path,
        master_df=master_df,
        horizon=horizon,
        use_only_complete_rows=args.use_only_complete_rows,
    )
    if len(horizon_df) <= args.initial_train_size:
        raise ValueError(
            f"No hay suficientes filas en {CURATED_BASE_SHEET_PREFIX}{horizon} para initial_train_size={args.initial_train_size}. "
            f"Filas_disponibles={len(horizon_df)}."
        )

    prediction_rows: list[dict[str, Any]] = []
    tuning_trace: list[dict[str, Any]] = []

    alpha_grid = np.logspace(args.alpha_grid_min_exp, args.alpha_grid_max_exp, args.alpha_grid_size).tolist()

    for test_idx in range(args.initial_train_size, len(horizon_df)):
        train_df = horizon_df.iloc[:test_idx].copy()
        test_row = horizon_df.iloc[test_idx]

        alpha_payload: dict[str, Any] | None = None
        if args.meta_model == "ridge":
            alpha_payload = select_best_alpha_time_series(
                train_data=train_df,
                feature_columns=feature_columns,
                target_column="y_true",
                estimator_builder=build_ridge_estimator,
                alpha_grid=alpha_grid,
                feature_mode="all",
                target_mode=TARGET_MODE_LEVEL,
                inner_splits=args.inner_splits,
                tuning_metric=args.alpha_selection_metric,
            )
            estimator = build_ridge_estimator(alpha_payload["best_alpha"])
            best_alpha = float(alpha_payload["best_alpha"])
        else:
            estimator = build_huber_estimator()
            best_alpha = None

        estimator.fit(train_df[feature_columns], train_df["y_true"])
        y_pred = float(estimator.predict(horizon_df.iloc[[test_idx]][feature_columns])[0])

        prediction_rows.append(
            build_prediction_record(
                test_row=test_row,
                feature_columns=feature_columns,
                horizon=horizon,
                run_id=args.run_id,
                meta_model=args.meta_model,
                y_pred=y_pred,
                alpha=best_alpha,
            )
        )
        tuning_trace.append(
            build_fold_trace(
                test_row=test_row,
                outer_fold_index=test_idx - args.initial_train_size + 1,
                feature_columns=feature_columns,
                alpha_payload=alpha_payload,
                fitted_estimator=estimator,
            )
        )

    predictions_df = pd.DataFrame(prediction_rows)
    metrics = compute_radar_metrics(predictions_df)
    loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
    base_comparison = build_base_metrics_on_eval_subset(
        predictions_df=predictions_df,
        feature_columns=feature_columns,
        horizon=horizon,
        reference_values=reference_values,
    )

    features_df = pd.DataFrame(
        {
            "feature_name": feature_columns,
            "source_run_id": feature_columns,
            "position": list(range(1, len(feature_columns) + 1)),
            "sheet_name": [f"{CURATED_BASE_SHEET_PREFIX}{horizon}"] * len(feature_columns),
        }
    )

    run.save_dataframe(
        predictions_df,
        f"predicciones_h{horizon}.csv",
        artifact_type="predicciones",
        notes=(
            "Predicciones OOF del meta-modelo de stacking sobre la base curada por horizonte. "
            "Incluye columnas base usadas por el meta-modelo."
        ),
    )
    run.save_dataframe(
        features_df,
        f"stacking_features_h{horizon}.csv",
        artifact_type="stacking_features",
        notes="Columnas base finales usadas por el meta-modelo en este horizonte.",
    )

    notas_config_payload = {
        "table_path": str(args.table_path),
        "sheet_name": f"{CURATED_BASE_SHEET_PREFIX}{horizon}",
        "meta_model": args.meta_model,
        "feature_columns": feature_columns,
        "use_only_complete_rows": args.use_only_complete_rows,
        "initial_train_size": args.initial_train_size,
        "rows_disponibles": int(len(horizon_df)),
        "rows_eval": int(len(predictions_df)),
        "alpha_grid_size": args.alpha_grid_size if args.meta_model == "ridge" else None,
        "alpha_selection_metric": args.alpha_selection_metric if args.meta_model == "ridge" else None,
        "inner_splits": args.inner_splits if args.meta_model == "ridge" else None,
    }

    return {
        "predictions": predictions_df,
        "feature_columns": feature_columns,
        "tuning_trace": tuning_trace,
        "base_comparison": base_comparison,
        "rows_summary": {
            "horizonte_sem": int(horizon),
            "sheet_name": f"{CURATED_BASE_SHEET_PREFIX}{horizon}",
            "rows_disponibles": int(len(horizon_df)),
            "rows_eval": int(len(predictions_df)),
            "rows_descartadas_inicio": int(args.initial_train_size),
            "feature_count": len(feature_columns),
            "feature_columns": feature_columns,
            "meta_model": args.meta_model,
            "use_only_complete_rows": bool(args.use_only_complete_rows),
        },
        "horizon_result": {
            "horizonte_sem": int(horizon),
            "target": TARGET_MODE_LEVEL,
            "variables_temporales": "predicciones_oof_modelos_base_por_horizonte",
            "variables_tematicas": ", ".join(feature_columns),
            "transformacion": "standard_scaler_meta" if args.meta_model in {"ridge", "huber"} else "",
            "seleccion_variables": "tabla_curada_e9_fila_completa",
            "validacion": "walk-forward_expanding_sobre_base_curada",
            "dataset_periodo": (
                f"{predictions_df[DATE_COLUMN].min().date()} a {predictions_df[DATE_COLUMN].max().date()}"
            ),
            "notas_config": json.dumps(notas_config_payload, ensure_ascii=False, sort_keys=True),
            "estado": "corrido",
            "comentarios": args.hypothesis_note,
            "loss_h": float(loss_h),
            **metrics,
        },
    }


def build_run_parameters(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "table_path": str(args.table_path),
        "dataset_path": str(args.dataset_path),
        "sheet_name": args.sheet_name,
        "target_mode": TARGET_MODE_LEVEL,
        "horizons": list(args.horizons),
        "initial_train_size": args.initial_train_size,
        "meta_model": args.meta_model,
        "alpha_grid_size": args.alpha_grid_size,
        "alpha_grid_min_exp": args.alpha_grid_min_exp,
        "alpha_grid_max_exp": args.alpha_grid_max_exp,
        "inner_splits": args.inner_splits,
        "alpha_selection_metric": args.alpha_selection_metric,
        "use_only_complete_rows": args.use_only_complete_rows,
        "curated_candidates_by_horizon": {str(key): list(value) for key, value in E9_CANDIDATES_BY_HORIZON.items()},
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    master_df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E9",
        family="stacking_controlado",
        model=f"stacking_{args.meta_model}_curado_por_horizonte",
        script_path=__file__,
        parametros=build_run_parameters(args),
    )

    horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    alpha_tuning_payload: dict[str, Any] = {
        "meta_model": args.meta_model,
        "alpha_selection_metric": args.alpha_selection_metric if args.meta_model == "ridge" else None,
        "alpha_grid": (
            np.logspace(args.alpha_grid_min_exp, args.alpha_grid_max_exp, args.alpha_grid_size).tolist()
            if args.meta_model == "ridge"
            else []
        ),
        "horizontes": {},
    }
    base_comparison_payload: dict[str, Any] = {
        "run_id": args.run_id,
        "meta_model": args.meta_model,
        "table_path": str(args.table_path),
        "comparacion_por_horizonte": [],
    }

    for horizon in args.horizons:
        horizon_output = run_stacking_for_horizon(
            args=args,
            run=run,
            master_df=master_df,
            reference_values=reference_values,
            horizon=horizon,
        )
        horizon_results.append(horizon_output["horizon_result"])
        rows_summary.append(horizon_output["rows_summary"])
        base_comparison_payload["comparacion_por_horizonte"].append(horizon_output["base_comparison"])
        alpha_tuning_payload["horizontes"][str(horizon)] = horizon_output["tuning_trace"]

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen de filas disponibles, filas evaluadas y columnas base por horizonte.",
    )
    run.save_json(
        alpha_tuning_payload,
        "alpha_tuning_horizontes.json",
        artifact_type="tuning",
        notes="Traza de tuning temporal interno del meta-modelo por horizonte.",
    )
    run.save_json(
        base_comparison_payload,
        "comparacion_bases_horizontes.json",
        artifact_type="comparacion",
        notes="Comparacion de E9 contra los modelos base sobre el mismo subset de evaluacion.",
    )

    total_radar = compute_total_radar_loss(
        horizon_results=horizon_results,
        reference_values=reference_values,
        l_coh=None,
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
        "meta_model": args.meta_model,
        "use_only_complete_rows": args.use_only_complete_rows,
        "initial_train_size": args.initial_train_size,
        "alpha_grid_size": args.alpha_grid_size if args.meta_model == "ridge" else None,
        "alpha_selection_metric": args.alpha_selection_metric if args.meta_model == "ridge" else None,
        "inner_splits": args.inner_splits if args.meta_model == "ridge" else None,
        "horizons": list(args.horizons),
        "candidate_columns": {str(key): list(E9_CANDIDATES_BY_HORIZON[key]) for key in args.horizons},
    }
    run.finalize(
        horizon_results=horizon_results,
        target=TARGET_MODE_LEVEL,
        variables_temporales="predicciones_oof_base_curada_por_horizonte",
        variables_tematicas=", ".join(
            sorted({run_id for horizon in args.horizons for run_id in E9_CANDIDATES_BY_HORIZON[horizon]})
        ),
        transformacion="standard_scaler_meta",
        seleccion_variables="tabla_curada_e9_fila_completa",
        validacion="walk-forward_expanding_sobre_base_curada",
        dataset_periodo=(
            f"{master_df[DATE_COLUMN].min().date()} a {master_df[DATE_COLUMN].max().date()}"
        ),
        notas_config=json.dumps(notas_config_payload, ensure_ascii=False, sort_keys=True),
        estado="corrido",
        comentarios=(
            f"{args.hypothesis_note} | stacking clasico controlado por horizonte "
            f"| L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        summary_metrics=total_radar,
    )

    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {total_radar['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
