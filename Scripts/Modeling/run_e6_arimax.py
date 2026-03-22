#!/usr/bin/env python3
from __future__ import annotations

import argparse

from custom_estimators import SarimaxRegressor
from pipeline_common import (
    add_common_experiment_args,
    finalize_common_args,
    parse_order,
    run_time_series_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E6 | Series de tiempo con exogenas via SARIMAX.",
    )
    add_common_experiment_args(parser, default_run_id="E6_v1")
    parser.add_argument("--order", default="1,0,0")
    parser.add_argument("--trend", default="c")
    parser.add_argument("--maxiter", type=int, default=200)
    args = finalize_common_args(parser.parse_args())
    args.order = parse_order(args.order)
    return args


def build_estimator(args: argparse.Namespace) -> SarimaxRegressor:
    return SarimaxRegressor(
        order=args.order,
        trend=args.trend,
        maxiter=args.maxiter,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "order": list(args.order),
        "trend": args.trend,
        "maxiter": args.maxiter,
    }


def main() -> None:
    args = parse_args()
    result = run_time_series_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E6",
        family="series_tiempo_exogenas",
        model_name="SARIMAX",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios="Series de tiempo con exogenas via SARIMAX.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
