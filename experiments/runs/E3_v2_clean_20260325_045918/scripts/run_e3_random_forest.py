#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor

from config import DEFAULT_RANDOM_STATE, TARGET_MODE_LEVEL
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    run_tabular_experiment,
)

TREE_MODEL_RANDOM_FOREST = "random_forest"
TREE_MODEL_EXTRA_TREES = "extra_trees"


def parse_optional_int(raw_value: str) -> int | None:
    token = raw_value.strip().lower()
    if token in {"none", "null"}:
        return None
    return int(token)


def parse_max_features(raw_value: str) -> str | float | int:
    token = raw_value.strip().lower()
    if token in {"sqrt", "log2"}:
        return token
    numeric_value = float(token)
    if numeric_value.is_integer() and numeric_value >= 1:
        return int(numeric_value)
    return numeric_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E3 | Familia de bagging con arboles: Random Forest o ExtraTrees bajo walk-forward temporal.",
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
    parser.add_argument(
        "--tree-model",
        choices=(TREE_MODEL_RANDOM_FOREST, TREE_MODEL_EXTRA_TREES),
        default=TREE_MODEL_RANDOM_FOREST,
    )
    parser.add_argument("--n-estimators", type=int, default=400)
    parser.add_argument(
        "--max-depth",
        default="6",
        help="Profundidad maxima. Usa 'none' para dejar el arbol sin tope.",
    )
    parser.add_argument("--min-samples-leaf", type=int, default=2)
    parser.add_argument("--min-samples-split", type=int, default=4)
    parser.add_argument("--max-features", default="sqrt")
    parser.add_argument("--bootstrap", dest="bootstrap", action="store_true")
    parser.add_argument("--no-bootstrap", dest="bootstrap", action="store_false")
    parser.set_defaults(bootstrap=True)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = finalize_common_args(parser.parse_args())
    args.max_depth = parse_optional_int(args.max_depth)
    args.max_features = parse_max_features(args.max_features)
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    return args


def build_estimator(args: argparse.Namespace):
    common_params = {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "min_samples_split": args.min_samples_split,
        "max_features": args.max_features,
        "bootstrap": args.bootstrap,
        "random_state": args.random_state,
        "n_jobs": -1,
    }
    if args.tree_model == TREE_MODEL_EXTRA_TREES:
        return ExtraTreesRegressor(**common_params)
    return RandomForestRegressor(**common_params)


def resolve_model_name(args: argparse.Namespace) -> str:
    if args.tree_model == TREE_MODEL_EXTRA_TREES:
        return "extra_trees_regressor"
    return "random_forest_regressor"


def resolve_hypothesis_label(args: argparse.Namespace) -> str:
    if args.hypothesis_note:
        return args.hypothesis_note
    if args.tree_model == TREE_MODEL_EXTRA_TREES:
        return "extra_trees_base"
    return "baseline_no_lineal"


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "tree_model": args.tree_model,
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
    model_name = resolve_model_name(args)
    model_label = "ExtraTrees" if args.tree_model == TREE_MODEL_EXTRA_TREES else "Random Forest"
    comentarios = (
        f"{model_label} limpio con walk-forward temporal | "
        f"hipotesis={resolve_hypothesis_label(args)} | "
        "sin escalado por naturaleza basada en arboles"
    )
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E3",
        family="arboles_boosting",
        model_name=model_name,
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
