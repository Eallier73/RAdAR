#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline

from config import (
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    FEATURE_MODE_ALL,
    TARGET_COLUMNS,
    TARGET_MODE_CHOICES,
    TARGET_MODE_LEVEL,
    TRANSFORM_MODE_CHOICES,
    TRANSFORM_MODE_STANDARD,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    walk_forward_predict_with_tscv_alpha_tuning,
)
from experiment_logger import DEFAULT_RUNS_DIR, DEFAULT_WORKBOOK, RadarExperimentTracker
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    build_notas_config,
    build_run_parameters,
    build_selected_features_summary,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    save_reference_comparisons,
    save_run_outputs,
)
from preprocessing import build_feature_transformer, describe_transform_mode
from representation_features import (
    REPRESENTATION_MODE_CHOICES,
    build_e12_model_frame,
    resolve_run_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E12 | Representacion enriquecida por horizonte con base lineal simple.",
    )
    add_common_experiment_args(parser, default_run_id="E12_v1_clean")
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=12,
        horizons="1,2,3,4",
        extra_reference_run_ids="E9_v2_clean,E1_v4_clean",
    )
    parser.add_argument(
        "--representation-mode",
        choices=REPRESENTATION_MODE_CHOICES,
        required=True,
        help="Modo de representacion: minimal, expanded o disagreement_only.",
    )
    parser.add_argument(
        "--representation-run-ids",
        default="",
        help="Runs fuente de predicciones archivadas separados por coma. Si se omite, usa el set canonico del modo.",
    )
    parser.add_argument(
        "--transform-mode",
        choices=TRANSFORM_MODE_CHOICES,
        default=TRANSFORM_MODE_STANDARD,
        help="Transformacion aplicada dentro del pipeline de Ridge.",
    )
    parser.add_argument("--winsor-lower-quantile", type=float, default=0.05)
    parser.add_argument("--winsor-upper-quantile", type=float, default=0.95)
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--alpha-grid-points", type=int, default=40)
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--alpha-selection-metric", choices=("mae", "rmse"), default="mae")
    args = finalize_common_args(parser.parse_args())
    if not 0.0 <= args.winsor_lower_quantile < args.winsor_upper_quantile <= 1.0:
        raise ValueError("Los cuantiles de winsor deben cumplir 0 <= lower < upper <= 1.")
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    args.representation_run_ids = parse_string_sequence(args.representation_run_ids)
    return args


def build_estimator(alpha: float, args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "transform",
                build_feature_transformer(
                    transform_mode=args.transform_mode,
                    winsor_lower_quantile=args.winsor_lower_quantile,
                    winsor_upper_quantile=args.winsor_upper_quantile,
                ),
            ),
            ("model", Ridge(alpha=float(alpha))),
        ]
    )


def build_alpha_grid(args: argparse.Namespace) -> list[float]:
    return list(np.logspace(args.alpha_grid_min_exp, args.alpha_grid_max_exp, args.alpha_grid_points))


def summarize_alpha_trace(alpha_trace: list[dict[str, Any]]) -> dict[str, Any]:
    best_alphas = [float(item["best_alpha"]) for item in alpha_trace]
    return {
        "best_alpha_mean": float(np.mean(best_alphas)),
        "best_alpha_median": float(np.median(best_alphas)),
        "best_alpha_min": float(np.min(best_alphas)),
        "best_alpha_max": float(np.max(best_alphas)),
        "best_alphas_by_fold": alpha_trace,
    }


def load_run_prediction_frame(workbook_path: Path, run_id: str, horizon: int) -> pd.DataFrame:
    run_dir = resolve_run_dir(workbook_path, run_id)
    path = run_dir / f"predicciones_h{horizon}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Predicciones faltantes para {run_id} h{horizon}: {path}")
    frame = pd.read_csv(path, usecols=[DATE_COLUMN, "y_current", "y_true", "y_pred"])
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    return frame


def build_same_subset_comparison_payload(
    *,
    workbook_path: Path,
    reference_run_id: str,
    predictions_by_horizon: dict[int, pd.DataFrame],
    reference_values: dict[str, Any],
) -> dict[str, Any]:
    comparison_rows: list[dict[str, Any]] = []
    current_results: list[dict[str, Any]] = []
    reference_results: list[dict[str, Any]] = []

    for horizon, current_predictions in predictions_by_horizon.items():
        reference_predictions = load_run_prediction_frame(workbook_path, reference_run_id, horizon).rename(
            columns={
                "y_current": "y_current_ref",
                "y_true": "y_true_ref",
                "y_pred": "y_pred_ref",
            }
        )
        merged = current_predictions[[DATE_COLUMN, "y_current", "y_true", "y_pred"]].merge(
            reference_predictions,
            on=DATE_COLUMN,
            how="inner",
        )
        if merged.empty:
            comparison_rows.append(
                {
                    "horizonte_sem": horizon,
                    "rows_eval_aligned": 0,
                    "reference_run_id": reference_run_id,
                }
            )
            continue

        if not np.allclose(merged["y_true"], merged["y_true_ref"], atol=1e-9, equal_nan=False):
            raise ValueError(f"y_true no coincide entre E12 y {reference_run_id} en H{horizon}.")
        if not np.allclose(merged["y_current"], merged["y_current_ref"], atol=1e-9, equal_nan=False):
            raise ValueError(f"y_current no coincide entre E12 y {reference_run_id} en H{horizon}.")

        current_eval = merged[[DATE_COLUMN, "y_current", "y_true", "y_pred"]].copy()
        reference_eval = merged[[DATE_COLUMN, "y_current", "y_true", "y_pred_ref"]].rename(
            columns={"y_pred_ref": "y_pred"}
        )

        current_metrics = compute_radar_metrics(current_eval[["y_true", "y_pred", "y_current"]])
        reference_metrics = compute_radar_metrics(reference_eval[["y_true", "y_pred", "y_current"]])
        current_loss = compute_loss_h(current_metrics, horizon, reference_values)
        reference_loss = compute_loss_h(reference_metrics, horizon, reference_values)

        current_results.append({"horizonte_sem": horizon, "loss_h": current_loss, **current_metrics})
        reference_results.append({"horizonte_sem": horizon, "loss_h": reference_loss, **reference_metrics})
        comparison_rows.append(
            {
                "horizonte_sem": horizon,
                "rows_eval_aligned": int(len(merged)),
                "reference_run_id": reference_run_id,
                "loss_h_e12": float(current_loss),
                "loss_h_reference": float(reference_loss),
                "delta_loss_h": float(current_loss - reference_loss),
                "mae_e12": float(current_metrics["mae"]),
                "mae_reference": float(reference_metrics["mae"]),
                "delta_mae": float(current_metrics["mae"] - reference_metrics["mae"]),
                "rmse_e12": float(current_metrics["rmse"]),
                "rmse_reference": float(reference_metrics["rmse"]),
                "delta_rmse": float(current_metrics["rmse"] - reference_metrics["rmse"]),
                "direction_accuracy_e12": float(current_metrics["direccion_accuracy"]),
                "direction_accuracy_reference": float(reference_metrics["direccion_accuracy"]),
                "delta_direction_accuracy": float(current_metrics["direccion_accuracy"] - reference_metrics["direccion_accuracy"]),
                "deteccion_caidas_e12": float(current_metrics["deteccion_caidas"]),
                "deteccion_caidas_reference": float(reference_metrics["deteccion_caidas"]),
                "delta_deteccion_caidas": float(current_metrics["deteccion_caidas"] - reference_metrics["deteccion_caidas"]),
            }
        )

    e12_total = compute_total_radar_loss(current_results, reference_values)["l_total_radar"] if current_results else None
    reference_total = compute_total_radar_loss(reference_results, reference_values)["l_total_radar"] if reference_results else None
    return {
        "reference_run_id": reference_run_id,
        "rows_horizonte_aligned": [
            {
                "horizonte_sem": row["horizonte_sem"],
                "rows_eval_aligned": row["rows_eval_aligned"],
            }
            for row in comparison_rows
        ],
        "l_total_radar_e12_same_subset": float(e12_total) if e12_total is not None else None,
        "l_total_radar_reference_same_subset": float(reference_total) if reference_total is not None else None,
        "delta_l_total_radar_same_subset": (
            float(e12_total - reference_total)
            if e12_total is not None and reference_total is not None
            else None
        ),
        "comparacion_por_horizonte": comparison_rows,
    }


def main() -> None:
    args = parse_args()
    alpha_grid = build_alpha_grid(args)
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)

    model_params = {
        "representation_mode": args.representation_mode,
        "representation_run_ids_override": list(args.representation_run_ids),
        "alpha_grid": alpha_grid,
        "inner_splits": args.inner_splits,
        "alpha_selection_metric": args.alpha_selection_metric,
        "transform_mode": args.transform_mode,
        "winsor_lower_quantile": args.winsor_lower_quantile,
        "winsor_upper_quantile": args.winsor_upper_quantile,
    }

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E12",
        family="representacion_enriquecida",
        model="ridge_representacion",
        script_path=__file__,
        parametros=build_run_parameters(
            args=args,
            model_name="ridge_representacion",
            feature_columns=base_feature_columns,
            model_params=model_params,
        ),
    )

    predictions_by_horizon: dict[int, pd.DataFrame] = {}
    horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    alpha_summary_payload: list[dict[str, Any]] = []
    representation_summary_payload: list[dict[str, Any]] = []
    inventory_frames: list[pd.DataFrame] = []
    dataset_periodo = f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}"

    for horizon in args.horizons:
        modeling_df, base_candidates, rep_columns, target_column, inventory_df, diagnostics = build_e12_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode=args.target_mode,
            workbook_path=args.workbook,
            representation_mode=args.representation_mode,
            source_run_ids_override=args.representation_run_ids or None,
        )

        predictions, alpha_trace = walk_forward_predict_with_tscv_alpha_tuning(
            estimator_builder=lambda alpha: build_estimator(alpha, args),
            alpha_grid=alpha_grid,
            data=modeling_df,
            feature_columns=base_candidates,
            target_column=target_column,
            actual_target_column=TARGET_COLUMNS[horizon],
            initial_train_size=args.initial_train_size,
            feature_mode=args.feature_mode,
            target_mode=args.target_mode,
            always_include_columns=rep_columns,
            inner_splits=args.inner_splits,
            tuning_metric=args.alpha_selection_metric,
        )
        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["transform_mode"] = args.transform_mode
        predictions["representation_mode"] = args.representation_mode
        predictions["representation_feature_count"] = len(rep_columns)
        predictions["representation_features"] = ",".join(rep_columns)
        predictions["representation_source_run_ids"] = ",".join(diagnostics["source_run_ids"])
        predictions["run_id"] = args.run_id
        predictions["model_name"] = "ridge_representacion"
        predictions_by_horizon[horizon] = predictions

        if args.feature_mode != FEATURE_MODE_ALL:
            selected_features_summary = build_selected_features_summary(predictions)
            run.save_dataframe(
                selected_features_summary,
                f"features_seleccionadas_h{horizon}.csv",
                artifact_type="seleccion_features",
                notes=(
                    "Resumen de features seleccionadas dentro del bloque base. "
                    "Las features de representacion se declaran ex ante y se incluyen siempre."
                ),
            )

        if not inventory_df.empty:
            inventory_frames.append(inventory_df)
            run.save_dataframe(
                inventory_df,
                f"inventario_columnas_representacion_h{horizon}.csv",
                artifact_type="constructos",
                notes=(
                    "Inventario de constructos de representacion usados en el horizonte. "
                    "Documenta definicion, fuente y validez temporal sin leakage."
                ),
            )

        alpha_summary = summarize_alpha_trace(alpha_trace)
        alpha_summary_payload.append(
            {
                "horizonte_sem": horizon,
                "representation_mode": args.representation_mode,
                "tuning_metric": args.alpha_selection_metric,
                "inner_splits": args.inner_splits,
                **alpha_summary,
            }
        )

        summary_row = {
            "horizonte_sem": horizon,
            "rows_modeling": len(modeling_df),
            "rows_eval": len(predictions),
            "feature_candidates_base": len(base_candidates),
            "feature_candidates": len(base_candidates),
            "representation_feature_count": len(rep_columns),
            "selected_feature_count_avg": float(predictions["selected_feature_count"].mean()),
            "selected_feature_count_min": int(predictions["selected_feature_count"].min()),
            "selected_feature_count_max": int(predictions["selected_feature_count"].max()),
            "selected_total_input_features_avg": float(predictions["selected_feature_count"].mean() + len(rep_columns)),
            "feature_mode": args.feature_mode,
            "target_mode": args.target_mode,
            "transform_mode": args.transform_mode,
            "representation_mode": args.representation_mode,
            "representation_source_run_ids": diagnostics["source_run_ids"],
            "representation_description": diagnostics["description"],
        }
        rows_summary.append(summary_row)
        representation_summary_payload.append(
            {
                "horizonte_sem": horizon,
                **diagnostics,
            }
        )

        metrics = compute_radar_metrics(predictions)
        loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": args.target_mode,
                "variables_temporales": f"y_t + lags {list(args.lags)} + representacion_archivada_h{horizon}",
                "variables_tematicas": ", ".join(base_feature_columns),
                "transformacion": describe_transform_mode(args.transform_mode),
                "seleccion_variables": args.feature_mode,
                "validacion": "walk-forward_expanding",
                "dataset_periodo": dataset_periodo,
                "notas_config": build_notas_config(
                    args=args,
                    model_name="ridge_representacion",
                    model_params={**model_params, **diagnostics},
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": (
                    f"E12 representacion {args.representation_mode} | "
                    f"rep_features={len(rep_columns)} | source_runs={','.join(diagnostics['source_run_ids'])}"
                ),
                "loss_h": loss_h,
                **metrics,
            }
        )

    save_run_outputs(run=run, predictions_by_horizon=predictions_by_horizon, rows_summary=rows_summary)
    run.save_json(
        alpha_summary_payload,
        "alpha_tuning_horizontes.json",
        artifact_type="tuning",
        notes="Best alpha por fold externo y resumen por horizonte para E12.",
    )
    run.save_json(
        representation_summary_payload,
        "resumen_representacion_horizontes.json",
        artifact_type="resumen",
        notes="Resumen por horizonte del bloque de representacion usado por E12.",
    )
    if inventory_frames:
        combined_inventory = pd.concat(inventory_frames, ignore_index=True)
        run.save_dataframe(
            combined_inventory,
            "inventario_columnas_representacion.csv",
            artifact_type="constructos",
            notes="Inventario consolidado de constructos de representacion usados en todos los horizontes.",
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
        subset_comparison_rows: list[dict[str, Any]] = []
        for reference_run_id in reference_run_ids:
            payload = build_same_subset_comparison_payload(
                workbook_path=tracker.workbook_path,
                reference_run_id=reference_run_id,
                predictions_by_horizon=predictions_by_horizon,
                reference_values=reference_values,
            )
            run.save_json(
                payload,
                f"comparacion_mismo_subset_vs_{reference_run_id}.json",
                artifact_type="comparacion",
                notes=f"Comparacion contra {reference_run_id} usando exactamente las fechas evaluadas por E12.",
            )
            for row in payload["comparacion_por_horizonte"]:
                subset_comparison_rows.append(row)
        if subset_comparison_rows:
            run.save_dataframe(
                pd.DataFrame(subset_comparison_rows),
                "comparacion_benchmarks_mismo_subset.csv",
                artifact_type="comparacion",
                notes="Comparacion por horizonte contra benchmarks usando el mismo subset evaluado por E12.",
            )

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)} + representacion enriquecida",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion=describe_transform_mode(args.transform_mode),
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(
            {
                "representation_mode": args.representation_mode,
                "rows_summary": rows_summary,
                "representation_summary": representation_summary_payload,
            },
            ensure_ascii=False,
        ),
        estado="corrido",
        comentarios=(
            f"E12 representacion {args.representation_mode} | "
            f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
    )


if __name__ == "__main__":
    main()
