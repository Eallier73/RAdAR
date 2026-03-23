#!/usr/bin/env python3
from __future__ import annotations

import argparse

from config import DEFAULT_RANDOM_STATE
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    run_tabular_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E4_v1_clean | Familia boosting con XGBoost bajo walk-forward temporal.",
    )
    add_common_experiment_args(parser, default_run_id="E4_v1_clean")
    parser.set_defaults(
        target_mode="nivel",
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument("--n-estimators", type=int, default=250)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--subsample", type=float, default=0.9)
    parser.add_argument("--colsample-bytree", type=float, default=0.9)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace):
    from xgboost import XGBRegressor

    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        random_state=args.random_state,
        n_jobs=4,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "learning_rate": args.learning_rate,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "random_state": args.random_state,
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E4",
        family="arboles_boosting",
        model_name="XGBRegressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios=(
            "XGBoost limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'boosting_base'} | "
            "sin escalado por naturaleza basada en arboles"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
