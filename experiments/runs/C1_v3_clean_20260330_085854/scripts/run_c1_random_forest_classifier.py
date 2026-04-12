#!/usr/bin/env python3
from __future__ import annotations

import argparse

from classification_pipeline_common import (
    add_common_classification_args,
    add_reference_comparison_args,
    finalize_common_classification_args,
    prepare_classification_references,
    run_classification_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="C1 | Familia RandomForestClassifier bajo walk-forward temporal.",
    )
    add_common_classification_args(parser, default_run_id="C1_v1_clean")
    parser.set_defaults(
        feature_mode="all",
        target_mode_clf="bandas_5clases",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="")
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--min-samples-leaf", type=int, default=4)
    parser.add_argument("--min-samples-split", type=int, default=8)
    parser.add_argument("--max-features", default="sqrt")
    parser.add_argument("--class-weight", default="balanced_subsample")
    return finalize_common_classification_args(parser.parse_args())


def build_estimator(args: argparse.Namespace):
    from sklearn.ensemble import RandomForestClassifier

    return RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        min_samples_split=args.min_samples_split,
        max_features=args.max_features,
        class_weight=args.class_weight,
        random_state=args.random_seed,
        n_jobs=4,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "min_samples_split": args.min_samples_split,
        "max_features": args.max_features,
        "class_weight": args.class_weight,
        "random_seed": args.random_seed,
        "uses_scaling": False,
        "tuning_strategy": "baseline_fijo_sin_tuning_interno",
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = prepare_classification_references(args.reference_run_id, args.extra_reference_run_ids)
    result = run_classification_experiment(
        args=args,
        script_path=__file__,
        experiment_id="C1",
        family="clasificacion_random_forest",
        model_name="random_forest_classifier",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        comentarios=(
            "RandomForestClassifier limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'rf_clasificacion_baseline'} | "
            "sin tuning interno | class_weight nativo por fold"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Clasificacion: {result['l_total_clasificacion']:.6f}")


if __name__ == "__main__":
    main()
