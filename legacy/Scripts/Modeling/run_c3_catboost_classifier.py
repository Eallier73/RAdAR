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
        description="C3 | Familia CatBoostClassifier multiclase bajo walk-forward temporal.",
    )
    add_common_classification_args(parser, default_run_id="C3_v1_clean")
    parser.set_defaults(
        feature_mode="all",
        target_mode_clf="bandas_5clases",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="")
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--l2-leaf-reg", type=float, default=5.0)
    parser.add_argument("--subsample", type=float, default=0.8)
    parser.add_argument("--loss-function", default="MultiClass")
    parser.add_argument("--eval-metric", default="MultiClass")
    return finalize_common_classification_args(parser.parse_args())


def build_estimator(args: argparse.Namespace):
    from catboost import CatBoostClassifier

    return CatBoostClassifier(
        iterations=args.iterations,
        depth=args.depth,
        learning_rate=args.learning_rate,
        l2_leaf_reg=args.l2_leaf_reg,
        bootstrap_type="Bernoulli",
        subsample=args.subsample,
        loss_function=args.loss_function,
        eval_metric=args.eval_metric,
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
        "eval_metric": args.eval_metric,
        "random_seed": args.random_seed,
        "uses_scaling": False,
        "uses_categorical_features": False,
        "tuning_strategy": "baseline_fijo_sin_tuning_interno",
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = prepare_classification_references(args.reference_run_id, args.extra_reference_run_ids)
    result = run_classification_experiment(
        args=args,
        script_path=__file__,
        experiment_id="C3",
        family="clasificacion_catboost",
        model_name="catboost_classifier",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        comentarios=(
            "CatBoostClassifier limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'catboost_clasificacion_baseline'} | "
            "sin tuning interno | sin variables categoricas explicitas"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Clasificacion: {result['l_total_clasificacion']:.6f}")


if __name__ == "__main__":
    main()
