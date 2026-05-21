#!/usr/bin/env python3
from __future__ import annotations

import argparse

from config import DATE_COLUMN, TARGET_MODE_LEVEL
from custom_estimators import ProphetExogenousRegressor
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    run_time_series_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E7 | Series de tiempo con exogenas via Prophet.",
    )
    add_common_experiment_args(parser, default_run_id="E7_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument("--changepoint-prior-scale", type=float, default=0.05)
    parser.add_argument(
        "--seasonality-mode",
        choices=("additive", "multiplicative"),
        default="additive",
    )
    parser.add_argument("--weekly-seasonality", action="store_true")
    parser.add_argument("--yearly-seasonality", action="store_true")
    parser.add_argument("--daily-seasonality", action="store_true")
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace) -> ProphetExogenousRegressor:
    return ProphetExogenousRegressor(
        date_column=DATE_COLUMN,
        changepoint_prior_scale=args.changepoint_prior_scale,
        seasonality_mode=args.seasonality_mode,
        weekly_seasonality=args.weekly_seasonality,
        yearly_seasonality=args.yearly_seasonality,
        daily_seasonality=args.daily_seasonality,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "changepoint_prior_scale": args.changepoint_prior_scale,
        "seasonality_mode": args.seasonality_mode,
        "weekly_seasonality": args.weekly_seasonality,
        "yearly_seasonality": args.yearly_seasonality,
        "daily_seasonality": args.daily_seasonality,
        "uses_scaling": False,
        "uses_categorical_features": False,
        "tuning_strategy": "baseline_fijo_sin_tuning_interno",
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    result = run_time_series_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E7",
        family="series_tiempo_exogenas",
        model_name="prophet_exogenous_regressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios=(
            "Prophet con regresores exogenos bajo walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'prophet_baseline'} | "
            f"changepoint_prior_scale={args.changepoint_prior_scale} | "
            f"seasonality_mode={args.seasonality_mode} | "
            f"weekly={args.weekly_seasonality} yearly={args.yearly_seasonality} daily={args.daily_seasonality} | "
            "baseline fijo sin tuning interno | "
            "sin escalado | "
            "sin estacionalidades agresivas en esta apertura | "
            "fecha integrada al pipeline via always_include_columns y seleccion de exogenas restringida al train de cada fold externo"
        ),
        always_include_columns=[DATE_COLUMN],
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
