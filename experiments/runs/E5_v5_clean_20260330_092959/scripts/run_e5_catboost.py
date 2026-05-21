#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import numpy as np

from config import DATE_COLUMN, DEFAULT_RANDOM_STATE, FEATURE_MODE_ALL, TARGET_COLUMNS, TARGET_MODE_LEVEL
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    walk_forward_predict,
    walk_forward_predict_with_tscv_param_tuning,
)
from experiment_logger import RadarExperimentTracker
from feature_engineering import build_model_frame
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    build_notas_config,
    build_run_parameters,
    build_selected_features_summary,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    parse_float_sequence,
    parse_int_sequence,
    save_reference_comparisons,
    save_run_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E5 | Familia boosting tabular con CatBoost bajo walk-forward temporal.",
    )
    add_common_experiment_args(parser, default_run_id="E5_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="all",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--l2-leaf-reg", type=float, default=3.0)
    parser.add_argument("--subsample", type=float, default=0.8)
    parser.add_argument("--loss-function", default="RMSE")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_STATE)
    parser.add_argument("--use-inner-tuning", action="store_true")
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--tuning-metric", choices=("mae", "rmse"), default="mae")
    parser.add_argument("--iterations-grid", default="")
    parser.add_argument("--depth-grid", default="")
    parser.add_argument("--learning-rate-grid", default="")
    parser.add_argument("--l2-leaf-reg-grid", default="")
    parser.add_argument("--subsample-grid", default="")
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    if args.iterations_grid:
        args.iterations_grid = parse_int_sequence(args.iterations_grid, label="iterations_grid")
    else:
        args.iterations_grid = ()
    if args.depth_grid:
        args.depth_grid = parse_int_sequence(args.depth_grid, label="depth_grid")
    else:
        args.depth_grid = ()
    if args.learning_rate_grid:
        args.learning_rate_grid = parse_float_sequence(args.learning_rate_grid, label="learning_rate_grid")
    else:
        args.learning_rate_grid = ()
    if args.l2_leaf_reg_grid:
        args.l2_leaf_reg_grid = parse_float_sequence(args.l2_leaf_reg_grid, label="l2_leaf_reg_grid")
    else:
        args.l2_leaf_reg_grid = ()
    if args.subsample_grid:
        args.subsample_grid = parse_float_sequence(args.subsample_grid, label="subsample_grid")
    else:
        args.subsample_grid = ()
    return args


def build_estimator(args: argparse.Namespace, overrides: dict[str, object] | None = None):
    from catboost import CatBoostRegressor

    params = {
        "iterations": args.iterations,
        "depth": args.depth,
        "learning_rate": args.learning_rate,
        "l2_leaf_reg": args.l2_leaf_reg,
        "subsample": args.subsample,
        "loss_function": args.loss_function,
        "random_seed": args.random_seed,
    }
    if overrides:
        params.update(overrides)

    return CatBoostRegressor(
        iterations=int(params["iterations"]),
        depth=int(params["depth"]),
        learning_rate=float(params["learning_rate"]),
        l2_leaf_reg=float(params["l2_leaf_reg"]),
        bootstrap_type="Bernoulli",
        subsample=float(params["subsample"]),
        loss_function=str(params["loss_function"]),
        random_seed=int(params["random_seed"]),
        verbose=False,
        allow_writing_files=False,
        thread_count=4,
    )


def build_param_grid(args: argparse.Namespace) -> dict[str, list[object]]:
    param_grid: dict[str, list[object]] = {}
    if args.iterations_grid:
        param_grid["iterations"] = list(args.iterations_grid)
    if args.depth_grid:
        param_grid["depth"] = list(args.depth_grid)
    if args.learning_rate_grid:
        param_grid["learning_rate"] = list(args.learning_rate_grid)
    if args.l2_leaf_reg_grid:
        param_grid["l2_leaf_reg"] = list(args.l2_leaf_reg_grid)
    if args.subsample_grid:
        param_grid["subsample"] = list(args.subsample_grid)
    return param_grid


def build_model_params(
    args: argparse.Namespace,
    param_grid: dict[str, list[object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "iterations": args.iterations,
        "depth": args.depth,
        "learning_rate": args.learning_rate,
        "l2_leaf_reg": args.l2_leaf_reg,
        "subsample": args.subsample,
        "loss_function": args.loss_function,
        "random_seed": args.random_seed,
        "uses_scaling": False,
        "uses_categorical_features": False,
        "tuning_strategy": (
            "tscv_param_grid_temporal"
            if args.use_inner_tuning
            else "baseline_fijo_sin_tuning_interno"
        ),
    }
    if args.use_inner_tuning:
        payload["inner_splits"] = args.inner_splits
        payload["tuning_metric"] = args.tuning_metric
        payload["param_grid"] = param_grid or {}
    return payload


def summarize_catboost_trace(
    catboost_trace: list[dict[str, object]],
    args: argparse.Namespace,
) -> dict[str, object]:
    def get_param(item: dict[str, object], key: str, default: float | int) -> float:
        best_params = item.get("best_params", {})
        if isinstance(best_params, dict) and key in best_params:
            return float(best_params[key])
        return float(default)

    best_iterations = [get_param(item, "iterations", args.iterations) for item in catboost_trace]
    best_depths = [get_param(item, "depth", args.depth) for item in catboost_trace]
    best_learning_rates = [get_param(item, "learning_rate", args.learning_rate) for item in catboost_trace]
    best_l2 = [get_param(item, "l2_leaf_reg", args.l2_leaf_reg) for item in catboost_trace]
    best_subsamples = [get_param(item, "subsample", args.subsample) for item in catboost_trace]
    return {
        "best_iterations_mean": float(np.mean(best_iterations)),
        "best_iterations_median": float(np.median(best_iterations)),
        "best_iterations_min": float(np.min(best_iterations)),
        "best_iterations_max": float(np.max(best_iterations)),
        "best_depth_mean": float(np.mean(best_depths)),
        "best_depth_median": float(np.median(best_depths)),
        "best_depth_min": float(np.min(best_depths)),
        "best_depth_max": float(np.max(best_depths)),
        "best_learning_rate_mean": float(np.mean(best_learning_rates)),
        "best_learning_rate_median": float(np.median(best_learning_rates)),
        "best_learning_rate_min": float(np.min(best_learning_rates)),
        "best_learning_rate_max": float(np.max(best_learning_rates)),
        "best_l2_leaf_reg_mean": float(np.mean(best_l2)),
        "best_l2_leaf_reg_median": float(np.median(best_l2)),
        "best_l2_leaf_reg_min": float(np.min(best_l2)),
        "best_l2_leaf_reg_max": float(np.max(best_l2)),
        "best_subsample_mean": float(np.mean(best_subsamples)),
        "best_subsample_median": float(np.median(best_subsamples)),
        "best_subsample_min": float(np.min(best_subsamples)),
        "best_subsample_max": float(np.max(best_subsamples)),
        "convergence_warning_events_total": int(
            sum(int(item.get("outer_fold_convergence_warning_events", 0)) for item in catboost_trace)
        ),
        "outer_folds_with_convergence_warning": int(
            sum(1 for item in catboost_trace if int(item.get("outer_fold_convergence_warning_events", 0)) > 0)
        ),
        "best_params_by_fold": catboost_trace,
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)
    param_grid = build_param_grid(args)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E5",
        family="arboles_boosting",
        model="catboost_regressor",
        script_path=__file__,
        parametros=build_run_parameters(
            args=args,
            model_name="catboost_regressor",
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
        if args.use_inner_tuning:
            predictions, catboost_trace = walk_forward_predict_with_tscv_param_tuning(
                estimator_builder=lambda params: build_estimator(args, params),
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
            tuning_summary = summarize_catboost_trace(catboost_trace, args)
            tuning_summary_payload.append(
                {
                    "horizonte_sem": horizon,
                    "tuning_metric": args.tuning_metric,
                    "inner_splits": args.inner_splits,
                    **tuning_summary,
                }
            )
        else:
            predictions = walk_forward_predict(
                estimator=build_estimator(args),
                data=modeling_df,
                feature_columns=modeling_features,
                target_column=target_column,
                actual_target_column=TARGET_COLUMNS[horizon],
                initial_train_size=args.initial_train_size,
                feature_mode=args.feature_mode,
                target_mode=args.target_mode,
            )
            tuning_summary = None

        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["transform_mode"] = ""
        predictions["run_id"] = args.run_id
        predictions["model_name"] = "catboost_regressor"
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
            "transform_mode": "",
        }
        if tuning_summary is not None:
            summary_row.update(
                {
                    "best_iterations_mean": tuning_summary["best_iterations_mean"],
                    "best_iterations_median": tuning_summary["best_iterations_median"],
                    "best_iterations_min": tuning_summary["best_iterations_min"],
                    "best_iterations_max": tuning_summary["best_iterations_max"],
                    "best_depth_mean": tuning_summary["best_depth_mean"],
                    "best_depth_median": tuning_summary["best_depth_median"],
                    "best_depth_min": tuning_summary["best_depth_min"],
                    "best_depth_max": tuning_summary["best_depth_max"],
                    "best_l2_leaf_reg_mean": tuning_summary["best_l2_leaf_reg_mean"],
                    "best_l2_leaf_reg_median": tuning_summary["best_l2_leaf_reg_median"],
                    "best_l2_leaf_reg_min": tuning_summary["best_l2_leaf_reg_min"],
                    "best_l2_leaf_reg_max": tuning_summary["best_l2_leaf_reg_max"],
                    "convergence_warning_events_total": tuning_summary["convergence_warning_events_total"],
                    "outer_folds_with_convergence_warning": tuning_summary["outer_folds_with_convergence_warning"],
                }
            )
        rows_summary.append(summary_row)

        metrics = compute_radar_metrics(predictions)
        loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": args.target_mode,
                "variables_temporales": f"y_t + lags {list(args.lags)}",
                "variables_tematicas": ", ".join(base_feature_columns),
                "transformacion": "sin_escalar",
                "seleccion_variables": args.feature_mode,
                "validacion": "walk-forward_expanding",
                "dataset_periodo": dataset_periodo,
                "notas_config": build_notas_config(
                    args=args,
                    model_name="catboost_regressor",
                    model_params=build_model_params(args, param_grid),
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": (
                    "CatBoost limpio con walk-forward temporal | "
                    f"hipotesis={args.hypothesis_note or 'catboost_base_tabular'} | "
                    + (
                        f"tuning temporal interno | metric={args.tuning_metric} | inner_splits={args.inner_splits} | "
                        if args.use_inner_tuning
                        else "baseline fijo sin tuning interno | "
                    )
                    + "sin escalado por naturaleza basada en arboles | "
                    + "sin variables categoricas explicitas, operando sobre features numericas"
                ),
                "loss_h": loss_h,
                **metrics,
            }
        )

    save_run_outputs(run=run, predictions_by_horizon=predictions_by_horizon, rows_summary=rows_summary)
    if tuning_summary_payload:
        run.save_json(
            tuning_summary_payload,
            "catboost_tuning_horizontes.json",
            artifact_type="tuning",
            notes="Mejores hiperparametros CatBoost por fold externo y resumen por horizonte.",
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

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion="sin_escalar",
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(rows_summary, ensure_ascii=False),
        estado="corrido",
        comentarios=(
            "CatBoost limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'catboost_base_tabular'} | "
            + (
                f"tuning interno TimeSeriesSplit | metric={args.tuning_metric} | inner_splits={args.inner_splits} | "
                if args.use_inner_tuning
                else "baseline fijo sin tuning interno | "
            )
            + f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        l_coh=None,
    )

    result = {
        "workbook_path": tracker.workbook_path,
        "run_dir": run.run_dir,
        "horizon_results": horizon_results,
        "rows_summary": rows_summary,
        "l_total_radar": total_radar["l_total_radar"],
    }
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
