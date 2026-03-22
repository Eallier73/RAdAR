#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sklearn.ensemble import RandomForestRegressor

from config import DEFAULT_RANDOM_STATE
from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E3 | Familia arboles con RandomForestRegressor.",
    )
    add_common_experiment_args(parser, default_run_id="E3_v1")
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--min-samples-leaf", type=int, default=2)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
        n_jobs=-1,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "random_state": args.random_state,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E3",
        family="arboles_boosting",
        model_name="RandomForestRegressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios="Familia arboles con RandomForestRegressor.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
