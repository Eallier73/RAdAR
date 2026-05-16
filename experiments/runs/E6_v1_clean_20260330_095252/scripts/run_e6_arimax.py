#!/usr/bin/env python3
from __future__ import annotations

import argparse

from custom_estimators import SarimaxRegressor
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    finalize_common_args,
    normalize_reference_run_ids,
    run_time_series_experiment,
)
from config import TARGET_MODE_LEVEL


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E6 | Series de tiempo con exogenas via SARIMAX.",
    )
    add_common_experiment_args(parser, default_run_id="E6_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument("--ar-order", type=int, default=1)
    parser.add_argument("--diff-order", type=int, default=0)
    parser.add_argument("--ma-order", type=int, default=1)
    parser.add_argument("--trend", default="c")
    parser.add_argument("--maxiter", type=int, default=200)
    args = finalize_common_args(parser.parse_args())
    return args


def build_estimator(args: argparse.Namespace) -> SarimaxRegressor:
    return SarimaxRegressor(
        order=(args.ar_order, args.diff_order, args.ma_order),
        trend=args.trend,
        maxiter=args.maxiter,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "order": [args.ar_order, args.diff_order, args.ma_order],
        "trend": args.trend,
        "maxiter": args.maxiter,
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
        experiment_id="E6",
        family="series_tiempo_exogenas",
        model_name="sarimax_regressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios=(
            "ARIMAX/SARIMAX con exogenas bajo walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'arimax_baseline'} | "
            f"order=({args.ar_order},{args.diff_order},{args.ma_order}) trend={args.trend} | "
            "baseline fijo sin tuning interno | "
            "sin escalado | "
            "seleccion de exogenas restringida al train de cada fold externo"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
