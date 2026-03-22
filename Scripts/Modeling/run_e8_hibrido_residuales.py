#!/usr/bin/env python3
from __future__ import annotations

import argparse

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import DEFAULT_RANDOM_STATE
from custom_estimators import ResidualHybridRegressor
from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E8 | Hibrido de residuales: RidgeCV + RandomForest sobre residuales.",
    )
    add_common_experiment_args(parser, default_run_id="E8_v1")
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--alpha-grid-points", type=int, default=31)
    parser.add_argument("--residual-n-estimators", type=int, default=250)
    parser.add_argument("--residual-max-depth", type=int, default=5)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> ResidualHybridRegressor:
    base_estimator = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                RidgeCV(
                    alphas=np.logspace(
                        args.alpha_grid_min_exp,
                        args.alpha_grid_max_exp,
                        args.alpha_grid_points,
                    )
                ),
            ),
        ]
    )
    residual_estimator = RandomForestRegressor(
        n_estimators=args.residual_n_estimators,
        max_depth=args.residual_max_depth,
        random_state=args.random_state,
        n_jobs=-1,
    )
    return ResidualHybridRegressor(
        base_estimator=base_estimator,
        residual_estimator=residual_estimator,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "ridge_alphas": list(
            np.logspace(
                args.alpha_grid_min_exp,
                args.alpha_grid_max_exp,
                args.alpha_grid_points,
            )
        ),
        "residual_n_estimators": args.residual_n_estimators,
        "residual_max_depth": args.residual_max_depth,
        "random_state": args.random_state,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E8",
        family="hibridos_ensembles",
        model_name="ResidualHybridRidgeRF",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="mixta",
        comentarios="Hibrido de residuales: RidgeCV + RandomForest.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
