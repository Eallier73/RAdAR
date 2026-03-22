#!/usr/bin/env python3
from __future__ import annotations

import argparse

from config import DEFAULT_RANDOM_STATE
from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E5 | Familia boosting con CatBoost.",
    )
    add_common_experiment_args(parser, default_run_id="E5_v1")
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--loss-function", default="RMSE")
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace):
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        iterations=args.iterations,
        depth=args.depth,
        learning_rate=args.learning_rate,
        loss_function=args.loss_function,
        random_seed=args.random_state,
        verbose=False,
        allow_writing_files=False,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "iterations": args.iterations,
        "depth": args.depth,
        "learning_rate": args.learning_rate,
        "loss_function": args.loss_function,
        "random_state": args.random_state,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E5",
        family="arboles_boosting",
        model_name="CatBoostRegressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios="Familia boosting con CatBoost.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
