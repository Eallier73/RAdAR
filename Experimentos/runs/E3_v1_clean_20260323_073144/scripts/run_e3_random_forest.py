#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sklearn.ensemble import RandomForestRegressor

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
        description="E3_v1_clean | Random Forest con walk-forward temporal y comparaciones contra referencias.",
    )
    add_common_experiment_args(parser, default_run_id="E3_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument("--n-estimators", type=int, default=400)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--min-samples-leaf", type=int, default=2)
    parser.add_argument("--min-samples-split", type=int, default=4)
    parser.add_argument("--max-features", default="sqrt")
    parser.add_argument("--bootstrap", dest="bootstrap", action="store_true")
    parser.add_argument("--no-bootstrap", dest="bootstrap", action="store_false")
    parser.set_defaults(bootstrap=True)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        min_samples_split=args.min_samples_split,
        max_features=args.max_features,
        bootstrap=args.bootstrap,
        random_state=args.random_state,
        n_jobs=-1,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "min_samples_split": args.min_samples_split,
        "max_features": args.max_features,
        "bootstrap": args.bootstrap,
        "random_state": args.random_state,
        "uses_scaling": False,
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)
    comentarios = (
        "Random Forest limpio con walk-forward temporal | "
        f"hipotesis={args.hypothesis_note or 'baseline_no_lineal'} | "
        "sin escalado por naturaleza basada en arboles"
    )
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E3",
        family="arboles_boosting",
        model_name="random_forest_regressor",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion="sin_escalar",
        comentarios=comentarios,
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
