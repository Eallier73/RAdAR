#!/usr/bin/env python3
from __future__ import annotations

import argparse

from config import DEFAULT_RANDOM_STATE, TARGET_MODE_LEVEL
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
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace):
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        iterations=args.iterations,
        depth=args.depth,
        learning_rate=args.learning_rate,
        l2_leaf_reg=args.l2_leaf_reg,
        bootstrap_type="Bernoulli",
        subsample=args.subsample,
        loss_function=args.loss_function,
        random_seed=args.random_seed,
        verbose=False,
        allow_writing_files=False,
        thread_count=4,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "iterations": args.iterations,
        "depth": args.depth,
        "learning_rate": args.learning_rate,
        "l2_leaf_reg": args.l2_leaf_reg,
        "subsample": args.subsample,
        "loss_function": args.loss_function,
        "random_seed": args.random_seed,
        "uses_scaling": False,
        "uses_categorical_features": False,
        "tuning_strategy": "baseline_fijo_sin_tuning_interno",
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E5",
        family="arboles_boosting",
        model_name="catboost_regressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios=(
            "CatBoost limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'catboost_base_tabular'} | "
            "baseline fijo sin tuning interno | "
            "sin escalado por naturaleza basada en arboles | "
            "sin variables categoricas explicitas, operando sobre features numericas"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
