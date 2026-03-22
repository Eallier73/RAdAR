#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E2 | Familia robusta con HuberRegressor.",
    )
    add_common_experiment_args(parser, default_run_id="E2_v1")
    parser.add_argument("--epsilon", type=float, default=1.35)
    parser.add_argument("--alpha", type=float, default=0.0001)
    parser.add_argument("--max-iter", type=int, default=500)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                HuberRegressor(
                    epsilon=args.epsilon,
                    alpha=args.alpha,
                    max_iter=args.max_iter,
                ),
            ),
        ]
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "epsilon": args.epsilon,
        "alpha": args.alpha,
        "max_iter": args.max_iter,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E2",
        family="robusto",
        model_name="HuberRegressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="estandarizada",
        comentarios="Familia robusta con HuberRegressor.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
