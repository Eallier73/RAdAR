#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from sklearn.linear_model import BayesianRidge
from sklearn.pipeline import Pipeline

from config import (
    DATE_COLUMN,
    FEATURE_MODE_ALL,
    FEATURE_MODE_CORR,
    TARGET_COLUMNS,
    TRANSFORM_MODE_CHOICES,
    TRANSFORM_MODE_STANDARD,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import compute_loss_h, compute_radar_metrics, compute_total_radar_loss, walk_forward_predict
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
    save_reference_comparisons,
    save_run_outputs,
)
from preprocessing import build_feature_transformer, describe_transform_mode


DEFAULT_BAYESIAN_LAGS = "1,2,3,4,5,6"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E1.1 v1 | Micro-rama diagnostica con BayesianRidge bajo el mismo marco temporal limpio de E1.",
    )
    add_common_experiment_args(parser, default_run_id="E1_1_v1_bayesian_base")
    add_reference_comparison_args(
        parser,
        default_reference_run_id="E1_v5_clean",
        include_hypothesis_note=True,
    )
    parser.set_defaults(
        lags=DEFAULT_BAYESIAN_LAGS,
        feature_mode=FEATURE_MODE_CORR,
        transform_mode=TRANSFORM_MODE_STANDARD,
    )
    parser.add_argument(
        "--transform-mode",
        choices=TRANSFORM_MODE_CHOICES,
        default=TRANSFORM_MODE_STANDARD,
        help="Transformacion aplicada dentro del pipeline lineal bayesiano.",
    )
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "transform",
                build_feature_transformer(
                    transform_mode=args.transform_mode,
                    winsor_lower_quantile=0.05,
                    winsor_upper_quantile=0.95,
                ),
            ),
            ("model", BayesianRidge()),
        ]
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    estimator = BayesianRidge()
    params = estimator.get_params()
    params["transform_mode"] = args.transform_mode
    params["uses_scaling"] = True
    params["tuning_strategy"] = "sin_tuning_externo_micro_rama_controlada"
    return params


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)

    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)
    model_params = build_model_params(args)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E1",
        family="lineal_regularizado",
        model="bayesian_ridge",
        script_path=__file__,
        parametros=build_run_parameters(
            args=args,
            model_name="bayesian_ridge",
            feature_columns=base_feature_columns,
            model_params=model_params,
        ),
    )

    predictions_by_horizon = {}
    horizon_results = []
    rows_summary = []
    dataset_periodo = f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}"

    for horizon in args.horizons:
        modeling_df, modeling_features, target_column = build_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode=args.target_mode,
        )
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

        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["transform_mode"] = args.transform_mode
        predictions["run_id"] = args.run_id
        predictions["model_name"] = "bayesian_ridge"
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
            "transform_mode": args.transform_mode,
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
                    model_name="bayesian_ridge",
                    model_params=model_params,
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": (
                    "Micro-rama tactica BayesianRidge sin tuning amplio | "
                    "comparacion limpia contra Ridge cerrado"
                ),
                "loss_h": float(loss_h),
                **metrics,
            }
        )

    save_run_outputs(run=run, predictions_by_horizon=predictions_by_horizon, rows_summary=rows_summary)

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
        "micro_branch": "E1.1 Bayesian",
        "target_mode": args.target_mode,
        "feature_mode": args.feature_mode,
        "transform_mode": args.transform_mode,
        "lags": list(args.lags),
        "initial_train_size": args.initial_train_size,
        "horizons": list(args.horizons),
        "model": "bayesian_ridge",
        "model_params": model_params,
    }
    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion=describe_transform_mode(args.transform_mode),
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(notas_config_payload, ensure_ascii=False, sort_keys=True),
        estado="corrido",
        comentarios=(
            f"{args.hypothesis_note or 'bayesianridge_micro_branch'} | "
            f"BayesianRidge controlado | "
            f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        l_coh=None,
    )

    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {total_radar['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
