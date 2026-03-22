#!/usr/bin/env python3
from __future__ import annotations

import argparse

from config import DATE_COLUMN
from custom_estimators import ProphetExogenousRegressor
from pipeline_common import add_common_experiment_args, finalize_common_args, run_time_series_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E7 | Series de tiempo con exogenas via Prophet.",
    )
    add_common_experiment_args(parser, default_run_id="E7_v1")
    parser.add_argument("--changepoint-prior-scale", type=float, default=0.05)
    parser.add_argument(
        "--seasonality-mode",
        choices=("additive", "multiplicative"),
        default="additive",
    )
    parser.add_argument("--weekly-seasonality", action="store_true")
    parser.add_argument("--yearly-seasonality", action="store_true")
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> ProphetExogenousRegressor:
    return ProphetExogenousRegressor(
        date_column=DATE_COLUMN,
        changepoint_prior_scale=args.changepoint_prior_scale,
        seasonality_mode=args.seasonality_mode,
        weekly_seasonality=args.weekly_seasonality,
        yearly_seasonality=args.yearly_seasonality,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "changepoint_prior_scale": args.changepoint_prior_scale,
        "seasonality_mode": args.seasonality_mode,
        "weekly_seasonality": args.weekly_seasonality,
        "yearly_seasonality": args.yearly_seasonality,
    }


def main() -> None:
    args = parse_args()
    result = run_time_series_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E7",
        family="series_tiempo_exogenas",
        model_name="ProphetExogenous",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios="Series de tiempo con exogenas via Prophet.",
        always_include_columns=[DATE_COLUMN],
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
