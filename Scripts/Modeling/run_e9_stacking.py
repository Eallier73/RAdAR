#!/usr/bin/env python3
from __future__ import annotations

import argparse

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import HuberRegressor, RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import DEFAULT_RANDOM_STATE
from custom_estimators import TimeSeriesStackingRegressor
from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E9 | Stacking temporal con bases lineales y arboles.",
    )
    add_common_experiment_args(parser, default_run_id="E9_v1")
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--alpha-grid-points", type=int, default=21)
    parser.add_argument("--rf-n-estimators", type=int, default=200)
    parser.add_argument("--rf-max-depth", type=int, default=5)
    parser.add_argument("--meta-splits", type=int, default=3)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> TimeSeriesStackingRegressor:
    ridge = Pipeline(
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
    huber = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", HuberRegressor()),
        ]
    )
    rf = RandomForestRegressor(
        n_estimators=args.rf_n_estimators,
        max_depth=args.rf_max_depth,
        random_state=args.random_state,
        n_jobs=-1,
    )
    meta_model = RidgeCV(
        alphas=np.logspace(
            args.alpha_grid_min_exp,
            args.alpha_grid_max_exp,
            args.alpha_grid_points,
        )
    )
    return TimeSeriesStackingRegressor(
        base_estimators=(
            ("ridge", ridge),
            ("huber", huber),
            ("rf", rf),
        ),
        final_estimator=meta_model,
        n_splits=args.meta_splits,
        min_train_size=max(12, args.initial_train_size // 2),
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "base_estimators": ["ridge", "huber", "rf"],
        "rf_n_estimators": args.rf_n_estimators,
        "rf_max_depth": args.rf_max_depth,
        "meta_splits": args.meta_splits,
        "random_state": args.random_state,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E9",
        family="hibridos_ensembles",
        model_name="TimeSeriesStacking",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="mixta",
        comentarios="Stacking temporal con Ridge, Huber y RandomForest.",
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
