#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline

from config import (
    DATE_COLUMN,
    FEATURE_MODE_ALL,
    TARGET_COLUMNS,
    TARGET_MODE_LEVEL,
    TRANSFORM_MODE_CHOICES,
    TRANSFORM_MODE_STANDARD,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    walk_forward_predict_with_tscv_param_tuning,
)
from experiment_logger import RadarExperimentTracker
from feature_engineering import build_model_frame
from pipeline_common import (
    add_common_experiment_args,
    build_comparison_payload,
    build_notas_config,
    build_run_parameters,
    build_selected_features_summary,
    finalize_common_args,
    parse_float_sequence,
    parse_int_sequence,
    save_run_outputs,
)
from preprocessing import build_feature_transformer, describe_transform_mode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E2_v1_clean | Huber limpio con tuning temporal interno por TimeSeriesSplit.",
    )
    add_common_experiment_args(parser, default_run_id="E2_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    parser.add_argument(
        "--reference-run-id",
        default="E1_v5_clean",
        help="Run_ID de referencia principal para artefactos comparativos.",
    )
    parser.add_argument(
        "--extra-reference-run-ids",
        default="",
        help="Run_IDs extra para comparaciones JSON, separados por coma.",
    )
    parser.add_argument(
        "--hypothesis-note",
        default="",
        help="Nota corta de la hipotesis del run para comentarios y grid.",
    )
    parser.add_argument(
        "--transform-mode",
        choices=TRANSFORM_MODE_CHOICES,
        default=TRANSFORM_MODE_STANDARD,
        help="Transformacion aplicada dentro del pipeline de Huber.",
    )
    parser.add_argument("--winsor-lower-quantile", type=float, default=0.05)
    parser.add_argument("--winsor-upper-quantile", type=float, default=0.95)
    parser.add_argument(
        "--epsilon-grid",
        default="1.1,1.2,1.35,1.5,1.75,2.0",
        help="Grid de epsilon para Huber, separado por comas.",
    )
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-6.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=-1.0)
    parser.add_argument("--alpha-grid-points", type=int, default=6)
    parser.add_argument(
        "--max-iter-grid",
        default="1000",
        help="Grid de max_iter para Huber, separado por comas.",
    )
    parser.add_argument(
        "--tol-grid",
        default="0.0001",
        help="Grid de tolerancias para Huber, separado por comas.",
    )
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--tuning-metric", choices=("mae", "rmse"), default="mae")
    args = finalize_common_args(parser.parse_args())
    if not 0.0 <= args.winsor_lower_quantile < args.winsor_upper_quantile <= 1.0:
        raise ValueError("Los cuantiles de winsor deben cumplir 0 <= lower < upper <= 1.")
    args.epsilon_grid = parse_float_sequence(args.epsilon_grid, label="epsilon_grid")
    args.max_iter_grid = parse_int_sequence(args.max_iter_grid, label="max_iter_grid")
    args.tol_grid = parse_float_sequence(args.tol_grid, label="tol_grid")
    args.extra_reference_run_ids = tuple(
        token.strip() for token in args.extra_reference_run_ids.split(",") if token.strip()
    )
    return args


def build_param_grid(args: argparse.Namespace) -> dict[str, list[float | int]]:
    return {
        "epsilon": list(args.epsilon_grid),
        "alpha": [
            float(value)
            for value in np.logspace(
                args.alpha_grid_min_exp,
                args.alpha_grid_max_exp,
                args.alpha_grid_points,
            )
        ],
        "max_iter": list(args.max_iter_grid),
        "tol": list(args.tol_grid),
    }


def build_estimator(params: dict[str, float | int], args: argparse.Namespace) -> Pipeline:
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
            (
                "model",
                HuberRegressor(
                    epsilon=float(params["epsilon"]),
                    alpha=float(params["alpha"]),
                    max_iter=int(params["max_iter"]),
                    tol=float(params["tol"]),
                ),
            ),
        ]
    )


def build_model_params(
    args: argparse.Namespace,
    param_grid: dict[str, list[float | int]],
) -> dict[str, object]:
    return {
        "param_grid": param_grid,
        "inner_splits": args.inner_splits,
        "tuning_metric": args.tuning_metric,
        "hypothesis_note": args.hypothesis_note,
        "transform_mode": args.transform_mode,
        "winsor_lower_quantile": args.winsor_lower_quantile,
        "winsor_upper_quantile": args.winsor_upper_quantile,
    }


def _summarize_numeric(values: list[float], prefix: str) -> dict[str, float]:
    return {
        f"{prefix}_mean": float(np.mean(values)),
        f"{prefix}_median": float(np.median(values)),
        f"{prefix}_min": float(np.min(values)),
        f"{prefix}_max": float(np.max(values)),
    }


def summarize_huber_trace(huber_trace: list[dict[str, object]]) -> dict[str, object]:
    best_epsilons = [float(item["best_params"]["epsilon"]) for item in huber_trace]
    best_alphas = [float(item["best_params"]["alpha"]) for item in huber_trace]
    best_max_iter = [float(item["best_params"]["max_iter"]) for item in huber_trace]
    best_tol = [float(item["best_params"]["tol"]) for item in huber_trace]
    return {
        **_summarize_numeric(best_epsilons, "best_epsilon"),
        **_summarize_numeric(best_alphas, "best_alpha"),
        **_summarize_numeric(best_max_iter, "best_max_iter"),
        **_summarize_numeric(best_tol, "best_tol"),
        "convergence_warning_events_total": int(
            sum(int(item.get("outer_fold_convergence_warning_events", 0)) for item in huber_trace)
        ),
        "outer_folds_with_convergence_warning": int(
            sum(1 for item in huber_trace if int(item.get("outer_fold_convergence_warning_events", 0)) > 0)
        ),
        "max_convergence_warning_events_per_outer_fold": int(
            max((int(item.get("outer_fold_convergence_warning_events", 0)) for item in huber_trace), default=0)
        ),
        "best_params_by_fold": huber_trace,
    }


def main() -> None:
    args = parse_args()
    param_grid = build_param_grid(args)

    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E2",
        family="robusto",
        model="huber_tscv",
        script_path=__file__,
        parametros=build_run_parameters(
            args=args,
            model_name="huber_tscv",
            feature_columns=base_feature_columns,
            model_params=build_model_params(args, param_grid),
        ),
    )

    predictions_by_horizon = {}
    horizon_results = []
    rows_summary = []
    tuning_summary_payload = []
    dataset_periodo = f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}"

    for horizon in args.horizons:
        modeling_df, modeling_features, target_column = build_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode=args.target_mode,
        )
        predictions, huber_trace = walk_forward_predict_with_tscv_param_tuning(
            estimator_builder=lambda params: build_estimator(params, args),
            param_grid=param_grid,
            data=modeling_df,
            feature_columns=modeling_features,
            target_column=target_column,
            actual_target_column=TARGET_COLUMNS[horizon],
            initial_train_size=args.initial_train_size,
            feature_mode=args.feature_mode,
            target_mode=args.target_mode,
            inner_splits=args.inner_splits,
            tuning_metric=args.tuning_metric,
        )

        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["transform_mode"] = args.transform_mode
        predictions["run_id"] = args.run_id
        predictions["model_name"] = "huber_tscv"
        predictions_by_horizon[horizon] = predictions

        if args.feature_mode != FEATURE_MODE_ALL:
            selected_features_summary = build_selected_features_summary(predictions)
            run.save_dataframe(
                selected_features_summary,
                f"features_seleccionadas_h{horizon}.csv",
                artifact_type="seleccion_features",
                notes=(
                    "Resumen de combinaciones de features seleccionadas por fold externo. "
                    "El filtro se calcula solo con el train de cada fold externo."
                ),
            )

        tuning_summary = summarize_huber_trace(huber_trace)
        tuning_summary_payload.append(
            {
                "horizonte_sem": horizon,
                "tuning_metric": args.tuning_metric,
                "inner_splits": args.inner_splits,
                **tuning_summary,
            }
        )

        summary_row = {
            "horizonte_sem": horizon,
            "rows_modeling": len(modeling_df),
            "rows_eval": len(predictions),
            "feature_candidates": len(modeling_features),
            "selected_feature_count_avg": float(predictions["selected_feature_count"].mean()),
            "selected_feature_count_min": int(predictions["selected_feature_count"].min()),
            "selected_feature_count_max": int(predictions["selected_feature_count"].max()),
            "feature_mode": args.feature_mode,
            "target_mode": args.target_mode,
            "transform_mode": args.transform_mode,
            "best_epsilon_mean": tuning_summary["best_epsilon_mean"],
            "best_epsilon_median": tuning_summary["best_epsilon_median"],
            "best_epsilon_min": tuning_summary["best_epsilon_min"],
            "best_epsilon_max": tuning_summary["best_epsilon_max"],
            "best_alpha_mean": tuning_summary["best_alpha_mean"],
            "best_alpha_median": tuning_summary["best_alpha_median"],
            "best_alpha_min": tuning_summary["best_alpha_min"],
            "best_alpha_max": tuning_summary["best_alpha_max"],
            "convergence_warning_events_total": tuning_summary["convergence_warning_events_total"],
            "outer_folds_with_convergence_warning": tuning_summary["outer_folds_with_convergence_warning"],
            "max_convergence_warning_events_per_outer_fold": tuning_summary[
                "max_convergence_warning_events_per_outer_fold"
            ],
        }
        rows_summary.append(summary_row)

        metrics = compute_radar_metrics(predictions)
        loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": args.target_mode,
                "variables_temporales": f"y_t + lags {list(args.lags)}",
                "variables_tematicas": ", ".join(base_feature_columns),
                "transformacion": describe_transform_mode(args.transform_mode),
                "seleccion_variables": args.feature_mode,
                "validacion": "walk-forward_expanding",
                "dataset_periodo": dataset_periodo,
                "notas_config": build_notas_config(
                    args=args,
                    model_name="huber_tscv",
                    model_params=build_model_params(args, param_grid),
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": (
                    "Huber limpio con tuning temporal interno | "
                    f"hipotesis={args.hypothesis_note or 'baseline_huber'} | "
                    f"metric={args.tuning_metric} | inner_splits={args.inner_splits}"
                ),
                "loss_h": loss_h,
                **metrics,
            }
        )

    save_run_outputs(run=run, predictions_by_horizon=predictions_by_horizon, rows_summary=rows_summary)
    run.save_json(
        tuning_summary_payload,
        "huber_tuning_horizontes.json",
        artifact_type="tuning",
        notes="Mejores hiperparametros Huber por fold externo y resumen por horizonte.",
    )

    total_radar = compute_total_radar_loss(
        horizon_results=horizon_results,
        reference_values=reference_values,
        l_coh=None,
    )
    comparison_run_ids = (args.reference_run_id, *args.extra_reference_run_ids)
    for reference_run_id in comparison_run_ids:
        comparison_payload = build_comparison_payload(
            workbook_path=args.workbook,
            reference_run_id=reference_run_id,
            clean_run_id=args.run_id,
            horizon_results=horizon_results,
            l_total_radar=float(total_radar["l_total_radar"]),
        )
        comparison_filename = f"comparacion_vs_{reference_run_id}.json"
        run.save_json(
            comparison_payload,
            comparison_filename,
            artifact_type="comparacion",
            notes=f"Comparacion de la corrida clean contra {reference_run_id}.",
        )

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion=describe_transform_mode(args.transform_mode),
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(rows_summary, ensure_ascii=False),
        estado="corrido",
        comentarios=(
            "Huber limpio con tuning interno TimeSeriesSplit | "
            f"hipotesis={args.hypothesis_note or 'baseline_huber'} | "
            f"metric={args.tuning_metric} | "
            f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        l_coh=None,
    )

    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {total_radar['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
